"""Auditoría independiente de darwinex/bonos_fin_de_mes.py (19-11-2026).

Rehace la prueba con otro método de precio y añade lo que la prueba original no miraba:
1. Precio del 10 años con un bono a la par exacto (cupón semestral = rendimiento de ayer), no con duración fija 8,5.
2. Placebo completo: las 3 sesiones que terminan en CADA posición del mes (no solo en la 12.ª), para ver en qué
   percentil cae la ventana de fin de mes y cuánto es deriva (los bonos subieron casi todo 1990-2020).
3. Futuro ZN real de Yahoo con los saltos de vencimiento detectados contra el precio de FRED, no con |r| < 2 %
   (ese filtro quita días reales grandes y deja saltos pequeños). Se cuentan los saltos que caen en la ventana.
Uso: python darwinex/bonos_fin_de_mes/auditoria.py datos_bonos
"""
import sys, os, numpy as np, pandas as pd

D = sys.argv[1] if len(sys.argv) > 1 else "datos_bonos"
COSTE = 3.0


def fred(s):
    d = pd.read_csv(os.path.join(D, s + ".csv")); d.columns = ["d", "v"]
    return pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()


def par(y_ayer, y_hoy, anios=10):
    """Retorno diario de un bono a la par emitido ayer (cupón = y_ayer) valorado hoy a y_hoy, más el devengo."""
    c, y, n = y_ayer / 100, y_hoy / 100, 2 * anios
    y = np.where(np.abs(y) < 1e-6, 1e-6, y)          # rendimiento 0 (Bund 2016-21): límite continuo
    v = (1 + y / 2) ** -n
    p = (c / y) * (1 - v) + v
    return p - 1 + c / 252


def t(x):
    x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))


def ventanas(r, ses=3):
    """Tabla mes × posición: retorno (pb) de las `ses` sesiones que terminan en la sesión k (k>0 desde el inicio,
    k<0 desde el final: −1 = última sesión)."""
    filas = {}
    for p, g in r.groupby(r.index.to_period("M")):
        if len(g) < 15: continue
        v = g.values * 1e4; f = {}
        for k in range(ses, 19): f[k] = v[k - ses:k].sum()
        for k in range(1, 9): f[-k] = v[len(v) - k - ses + 1:len(v) - k + 1].sum()
        filas[g.index[-1]] = f
    return pd.DataFrame(filas).T.sort_index()


def linea(nom, x):
    x = pd.Series(x).dropna(); n = x - COSTE; h = len(n) // 2
    print(f"{nom:44s} n {len(x):4d} | bruto {x.mean():6.2f} pb | neto {n.mean():6.2f} (t {t(n):5.2f}) | "
          f"1ª mitad {n.iloc[:h].mean():6.2f} 2ª {n.iloc[h:].mean():6.2f} | x2 {(x - 2 * COSTE).mean():6.2f}")


y = fred("DGS10")
r_par = pd.Series(par(y.shift(1).values, y.values), y.index).dropna()
r_dur = (-8.5 * y.diff() / 100 + y.shift(1) / 100 / 252).dropna()
tb = fred("DTB3").reindex(y.index).ffill()
r_exc = (r_par - tb.shift(1) / 100 / 252).dropna()

print("1) MISMA REGLA, OTRO PRECIO (bono a la par exacto)")
for nom, r in [("duración fija 8,5 (original)", r_dur), ("bono a la par exacto", r_par), ("par, en exceso de la letra", r_exc)]:
    w = ventanas(r)[-1]
    linea(nom + " 1990-2026", w["1990":"2026"])
    linea(nom + " 2019-2026", w["2019":"2026"])

print("\n2) PLACEBO COMPLETO: 3 sesiones terminando en cada posición del mes (bono a la par, 1990-2026, bruto pb)")
for nom, r in [("precio", r_par), ("exceso de la letra", r_exc)]:
    W = ventanas(r)["1990":"2026"]
    m = W.mean(); fin = m[-1]
    otras = m.drop([-1, -2, -3])                      # quita las que se solapan con la ventana de fin de mes
    print(f"   {nom}: fin de mes {fin:5.1f} | resto media {otras.mean():5.1f} sd {otras.std():4.1f} | "
          f"máximo del resto {otras.max():5.1f} (pos {otras.idxmax()}) | percentil {(otras < fin).mean() * 100:.0f}")
    print("     ", " ".join(f"{k}:{v:.1f}" for k, v in m.items()))
    dif = W[-1] - W[otras.index].mean(axis=1)          # fin de mes menos la media de las demás ventanas del mismo mes
    print(f"     fin de mes − media del resto del mismo mes: {dif.mean():5.1f} pb t {t(dif):4.2f} | "
          f"2019-26 {dif['2019':].mean():5.1f} pb t {t(dif['2019':]):4.2f}")

print("\n3) FUTURO ZN REAL (Yahoo) con vencimientos detectados contra FRED")
z = pd.read_csv(os.path.join(D, "ZN.csv"), index_col=0, parse_dates=True)["Close"].astype(float)
zr = z.pct_change().dropna()
ref = r_par.reindex(zr.index)
dif = (zr - ref)
sd = dif.rolling(250, min_periods=60).std().shift(1)
salto = (dif.abs() > 4 * sd) & ref.notna()
print(f"   días marcados como salto: {salto.sum()} de {len(zr)} ({salto.sum() / len(zr) * 100:.1f} %)")
zl = zr.where(~salto, ref)                              # el día de salto se sustituye por el retorno de FRED
zl = zl.dropna()
wz_raw = ventanas(zr)[-1]; wz = ventanas(zl)[-1]
saltos_m = salto.groupby(salto.index.to_period("M")).apply(lambda s: s.iloc[-3:].sum())
print(f"   meses con salto dentro de la ventana: {int((saltos_m > 0).sum())}")
linea("ZN sin limpiar 2000-2026", wz_raw["2001":"2026"])
linea("ZN limpio 2001-2026", wz["2001":"2026"])
linea("ZN limpio 2019-2026", wz["2019":"2026"])
Wz = ventanas(zl)["2001":"2026"]; mz = Wz.mean(); oz = mz.drop([-1, -2, -3])
print(f"   ZN placebo completo: fin de mes {mz[-1]:5.1f} | resto media {oz.mean():5.1f} máx {oz.max():5.1f} (pos {oz.idxmax()}) "
      f"| percentil {(oz < mz[-1]).mean() * 100:.0f}")
dz = Wz[-1] - Wz[oz.index].mean(axis=1)
print(f"   ZN fin de mes − resto del mismo mes: {dz.mean():5.1f} pb t {t(dz):4.2f}")
print("   ZN neto por año (pb):", {k: round(v) for k, v in (wz["2001":] - COSTE).groupby(wz["2001":].index.year).sum().items()})
w_fred = ventanas(r_par)[-1].reindex(wz.index)
print(f"   correlación ventana ZN vs FRED por mes: {wz.corr(w_fred):.3f}; ZN/FRED media {wz['2001':].mean() / w_fred['2001':].mean():.2f}")
pd.DataFrame({"zn_limpio_pb": wz, "fred_par_pb": w_fred}).to_csv(os.path.join(os.path.dirname(__file__), "ventanas_zn.csv"))
