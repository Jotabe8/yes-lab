"""Prueba del PREREGISTRO_BONOS_FIN_DE_MES.md. Uso: python darwinex/bonos_fin_de_mes.py datos_bonos"""
import sys, os, numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "datos_bonos"
DUR = {5: 4.6, 10: 8.5, 30: 17.0}
REFI = {2, 5, 8, 11}
COSTE = 3.0


def fred(s):
    d = pd.read_csv(os.path.join(D, s + ".csv")); d.columns = ["d", "v"]
    return pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()


def retornos(k):
    y = fred(f"DGS{k}")
    return (-DUR[k] * y.diff() / 100 + y.shift(1) / 100 / 252).dropna()


def ventana(r, fin=None, ses=3):
    """Retorno (pb) de las `ses` sesiones que acaban en la última del mes (fin=None) o en la sesión `fin`."""
    filas = []
    for p, g in r.groupby(r.index.to_period("M")):
        if len(g) < 15: continue
        j = len(g) if fin is None else fin
        filas.append((g.index[j - 1], g.iloc[j - ses:j].sum() * 1e4))
    return pd.Series(dict(filas)).sort_index()


def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan


def linea(nom, x, coste=COSTE):
    x = pd.Series(x).dropna(); n = x - coste; h = len(n) // 2
    print(f"{nom:46s} n {len(x):4d} | bruto {x.mean():6.2f} pb (t {t(x):5.2f}) | neto {n.mean():6.2f} (t {t(n):5.2f})"
          f" | 1ª mitad {n.iloc[:h].mean():6.2f} 2ª {n.iloc[h:].mean():6.2f} | x2 {(x - 2 * coste).mean():6.2f}")
    return n


r10 = retornos(10)
s, plac = ventana(r10), ventana(r10, fin=12)
refi = s[s.index.month.isin(REFI)]; otros = s[~s.index.month.isin(REFI)]
print("PRINCIPAL: 10 años, 3 últimas sesiones (pb; coste 3 pb)")
n = linea("1990-2026 (principal)", s["1990":"2026"])
linea("   placebo: 3 sesiones hasta la 12.ª", plac["1990":"2026"])
linea("2019-2026 (fuera de la muestra publicada)", s["2019":"2026"])
print("SECUNDARIA: meses de refinanciación (feb, may, ago, nov)")
linea("refinanciación 1990-2026", refi["1990":"2026"])
linea("resto de meses 1990-2026", otros["1990":"2026"])
linea("refinanciación 1990-2015 (no mirado con ETF)", refi["1990":"2015"])
linea("resto 1990-2015", otros["1990":"2015"])
linea("refinanciación 2016-2026", refi["2016":"2026"])
linea("resto 2016-2026", otros["2016":"2026"])
print("INFORMATIVO")
linea("1962-1989 (antes de la muestra publicada)", s["1962":"1989"])
for k in (5, 30):
    sk = ventana(retornos(k))
    linea(f"{k} años 1990-2026", sk["1990":"2026"])
x = s["1990":"2026"] - COSTE
print("Por año (neto pb):", {k: round(v, 1) for k, v in x.groupby(x.index.year).sum().items()})
print("Años positivos:", f"{(x.groupby(x.index.year).sum() > 0).mean():.0%}")
print("Por mes del calendario (bruto pb, 1990-2026):",
      {m: round(v, 1) for m, v in s["1990":"2026"].groupby(s["1990":"2026"].index.month).mean().items()})
anual = x.groupby(x.index.year).sum()
print(f"Rentabilidad anual media sin apalancar {anual.mean():.0f} pb; Sharpe anual neto {x.mean() / x.std() * np.sqrt(12):.2f}")
print("ROBUSTEZ (no decide)")
tb = fred("DTB3").reindex(r10.index).ffill()
ex = (r10 - tb.shift(1) / 100 / 252).dropna()
se, pe = ventana(ex), ventana(ex, fin=12)
linea("exceso sobre la letra a 3 meses, 1990-2026", se["1990":"2026"])
linea("   placebo exceso", pe["1990":"2026"])
linea("exceso 2019-2026", se["2019":"2026"])
z = pd.read_csv(os.path.join(D, "ZN.csv"), index_col=0, parse_dates=True)
zc = z["Close"].astype(float) if "Close" in z else z.iloc[:, 0].astype(float)
zr = zc.pct_change().dropna()
zr = zr[zr.abs() < 0.02]                                   # quita saltos de vencimiento del continuo
sz = ventana(zr)
linea(f"futuro ZN continuo (Yahoo) {sz.index[0].year}-2026", sz)
linea("   ZN 2019-2026", sz["2019":"2026"])
