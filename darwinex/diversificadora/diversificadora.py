"""Pata diversificadora para el DARWIN del ORB US100 (PREREGISTRO.md, 16-11-2026).
Uso (desde la raíz de yes-lab): python darwinex/diversificadora/diversificadora.py"""
import numpy as np, pandas as pd, os
np.random.seed(0)
AQUI = os.path.dirname(os.path.abspath(__file__))
F = "datos_diversificadora"; B = "datos_bonos"

def yahoo(n, carpeta=F):
    d = pd.read_csv(os.path.join(carpeta, n + ".csv"), index_col=0, parse_dates=True)
    c = pd.to_numeric(d["Close"], errors="coerce").dropna(); return c[c > 0]
def fred(n):
    d = pd.read_csv(os.path.join(B, n + ".csv")); d.columns = ["d", "v"]
    return pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()
def oro_spot():
    p = []
    for f in sorted(os.listdir("datos_oro/antes2012")) + sorted(os.listdir("datos_oro")):
        if not ("xauusd" in f and "bid" in f): continue
        ruta = os.path.join("datos_oro/antes2012" if "2003" in f else "datos_oro", f)
        d = pd.read_csv(ruta)
        t = pd.to_datetime(d.iloc[:, 0], unit="ms") if np.issubdtype(d.iloc[:, 0].dtype, np.number) else pd.to_datetime(d.iloc[:, 0])
        p.append(pd.Series(d["close"].values if "close" in d else d.iloc[:, 4].values, t))
    s = pd.concat(p).sort_index(); s = s[~s.index.duplicated()]
    s = s[s.index.hour <= 18]                      # ~13:30-14:00 NY, cerca del settlement del GC
    return s.groupby(s.index.normalize()).last()

dias = pd.bdate_range("2000-01-01", "2026-11-13")
rf = (fred("DTB3").reindex(pd.date_range("1990", "2026-12-31")).ffill().reindex(dias) / 100 / 252)
y7 = fred("DGS7") / 100

def limpia(fut, proxy, nombre):
    """Rendimiento diario del futuro; en días de roll (|futuro − sustituto| > 4 sd) se usa el sustituto."""
    rf_ = fut.pct_change(); rp = proxy
    j = pd.concat([rf_, rp], axis=1, keys=["f", "p"]).dropna()
    dif = j.f - j.p; sd = (dif - dif.median()).abs().median() * 1.4826
    salto = (dif - dif.median()).abs() > 4 * sd
    r = rf_.copy(); r[salto[salto].index] = j.p[salto]
    print(f"  {nombre}: {int(salto.sum())} días sustituidos, suma de saltos quitados {dif[salto].sum()*100:+.1f} %, "
          f"corr diaria futuro-sustituto {j.f.corr(j.p):.3f}")
    return r.reindex(dias)

print("Limpieza de rolls")
es = yahoo("ES"); spx = yahoo("GSPC", B)
r_es = limpia(es, spx.pct_change() - (rf.reindex(spx.index) - 0.018 / 252), "ES")
zn = yahoo("ZN")
dy = y7.diff(); carry = (y7.shift(1) / 252) - rf.reindex(y7.index)
r_zn = limpia(zn, -6.5 * dy + carry, "ZN")
gc = yahoo("GC"); xau = oro_spot()
r_gc = limpia(gc, xau.pct_change() - rf.reindex(xau.index), "GC")

def roll_cal(r, f):
    d = r.index; m = pd.Series(False, d)
    m[:] = f(d); r = r.copy(); r[m.values] = np.nan; return r
r_cl = roll_cal(yahoo("CL").pct_change().reindex(dias), lambda d: (d.day >= 19) & (d.day <= 25))
r_hg = roll_cal(yahoo("HG").pct_change().reindex(dias),
                lambda d: np.isin(d.month, [2, 4, 6, 8, 11]) & (d.day >= 24) | np.isin(d.month, [3, 5, 7, 9, 12]) & (d.day <= 3))

ROLLS = {"ES": 4, "ZN": 4, "GC": 6, "CL": 12, "HG": 5}
def pata(rets, clases):
    X = pd.DataFrame(rets).where(lambda x: x.abs() < 0.25)
    vol = np.sqrt((X ** 2).ewm(span=60, min_periods=40).mean() * 252)
    w = 1 / vol
    # igual riesgo por clase, igual riesgo dentro de la clase
    for cl, miembros in clases.items():
        w[miembros] = w[miembros].div(w[miembros].notna().sum(axis=1), axis=0)
    nclases = sum(w[m].notna().any(axis=1).astype(int) for m in clases.values())
    w = w.div(nclases, axis=0) * 0.10
    fm = pd.Series(X.index.isin(X.index.to_series().groupby(X.index.to_period("M")).last().values), X.index)
    w = w[fm].reindex(X.index).ffill().shift(1)
    bruto = (w * X).sum(axis=1, min_count=1)
    rv = bruto.rolling(252, min_periods=200).std() * np.sqrt(252)
    k = (0.10 / rv).clip(upper=3)[fm].reindex(rv.index).ffill().shift(1)
    wk = w.mul(k, axis=0)
    bruto = (wk * X.fillna(0)).sum(axis=1)
    coste = wk.diff().abs().sum(axis=1) * 0.0002 + sum(wk[c].abs().fillna(0) * 0.0002 * ROLLS[c] / 252 for c in wk)
    neto = (bruto - coste)[k.notna()]
    return neto, wk

P, wP = pata({"ES": r_es, "ZN": r_zn, "GC": r_gc}, {"acc": ["ES"], "bon": ["ZN"], "oro": ["GC"]})
P4, _ = pata({"ES": r_es, "ZN": r_zn, "GC": r_gc, "CL": r_cl, "HG": r_hg},
             {"acc": ["ES"], "bon": ["ZN"], "oro": ["GC"], "mp": ["CL", "HG"]})

def sr(m): return m.mean() / m.std() * np.sqrt(12)
def dd(m): c = m.cumsum(); return (c.cummax() - c).max()
def v6(m): return (m.rolling(6).sum() > 0).mean() * 100

print("\n1) Pata sola (mensual, neto)")
for nom, s in [("P  ES+ZN+GC", P), ("P4 +CL+HG (informativa)", P4)]:
    m = s.resample("ME").sum()
    for a, b in [("2003", "2026-10"), ("2003", "2011"), ("2012", "2017"), ("2018", "2026-10")]:
        x = m[a:b]; print(f"  {nom:24s} {a}-{b[:4]}: ret/año {x.mean()*1200:5.2f} %  vol {x.std()*np.sqrt(12)*100:5.2f} %  "
                          f"SR {sr(x):5.2f}  t {sr(x)*np.sqrt(len(x)/12):5.2f}  peor DD {dd(x)*100:5.1f} %")
    a = s.resample("YE").sum() * 100
    print("   por año:", " ".join(f"{d.year % 100:02d}:{v:+.0f}" for d, v in a["2003":].items()))

orb = pd.read_csv(os.path.join(AQUI, "serie_v018_be.csv"), parse_dates=["d"]).set_index("d")
o = (orb.Rbe - 0.05).resample("ME").sum()["2018-01":"2026-10"]
r12 = pd.read_csv(os.path.join(AQUI, "orb_us100_2012_2026.csv"), parse_dates=["fecha"]).set_index("fecha")
o12 = (r12.bruto - 0.05).resample("ME").sum()["2012-02":"2026-10"]

def mezcla(o, s, ratio=0.5):
    j = pd.concat([o, s], axis=1, keys=["o", "s"]).dropna()
    w = ratio * j.o.std() / j.s.std()
    mix = j.o + w * j.s; mix = mix * j.o.std() / mix.std()
    return j, w, mix
def fila(nom, x):
    print(f"  {nom:44s} SR {sr(x):5.2f}  peor DD {dd(x):5.1f} R  6 m positivas {v6(x):5.1f} %  "
          f"peor mes {x.min():5.1f} R  VaR95 mensual {-np.percentile(x,5):4.1f} R")

print("\n2-4) DARWIN 2018-01 → 2026-10 (todo en R del ORB, mezcla a la volatilidad del ORB)")
resumen = {}
for nom, s in [("P", P), ("P4", P4)]:
    sm = s.resample("ME").sum()
    j, w, mix = mezcla(o, sm)
    print(f" {nom}: correlación mensual con el ORB {j.o.corr(j.s):+.3f}; peso {w:.1f} R por unidad de rendimiento")
    fila("ORB solo", j.o); fila(f"ORB + {nom} (peso fijo 0,5)", mix)
    _, _, mixh = mezcla(o, sm - sm["2018":"2026-10"].mean() * 0.5)
    fila(f"ORB + {nom} con prima a la mitad", mixh)
    _, _, mix0 = mezcla(o, sm - sm["2018":"2026-10"].mean())
    fila(f"placebo: ORB + {nom} con media cero", mix0)
    for ratio in (0.25, 0.75, 1.0):
        _, _, mr = mezcla(o, sm, ratio); fila(f"   (informativo) peso {ratio}", mr)
    resumen[nom] = (j, w, mix, mixh)

print("\n5) Bootstrap por bloques de 3 meses (10.000) y desfases aleatorios, pata P")
j, w, mix, mixh = resumen["P"]
oo, ss = j.o.values, j.s.values; L = len(oo); d_real = sr(pd.Series(oo + w * ss)) - sr(pd.Series(oo))
rng = np.random.default_rng(1); ds = []
for _ in range(10000):
    st = rng.integers(0, L - 3, L // 3 + 1); ix = np.concatenate([np.arange(a, a + 3) for a in st])[:L]
    ds.append(sr(pd.Series(oo[ix] + w * ss[ix])) - sr(pd.Series(oo[ix])))
ds = np.array(ds)
print(f"  ΔSharpe real {d_real:+.3f}; bootstrap mediana {np.median(ds):+.3f}, p10 {np.percentile(ds,10):+.3f}, P(Δ>0) {(ds>0).mean()*100:.1f} %")
dsh = np.array([sr(pd.Series(oo + w * np.roll(ss, k))) - sr(pd.Series(oo)) for k in range(1, L)])
print(f"  desfases circulares ({L-1}): mediana {np.median(dsh):+.3f}; el real queda en el percentil {(dsh < d_real).mean()*100:.0f}")

print("\n   Control 2012-02 → 2026-10 con la réplica del ORB (bruto − 0,05 R)")
for nom, s in [("P", P), ("P4", P4)]:
    j2, w2, mx2 = mezcla(o12, s.resample("ME").sum())
    print(f"  {nom}: corr {j2.o.corr(j2.s):+.3f}"); fila("réplica ORB solo", j2.o); fila(f"réplica ORB + {nom}", mx2)
    for a, b in [("2012", "2017"), ("2018", "2026-10")]:
        print(f"     {a}-{b[:4]}: ORB SR {sr(j2.o[a:b]):5.2f}  mezcla SR {sr(mx2[a:b]):5.2f}")

print("\n   Meses malos del ORB (peor 20 %) y qué hizo la pata P ese mes")
q = j.o <= j.o.quantile(0.2)
print(f"  ORB medio {j.o[q].mean():+.2f} R; pata {j.s[q].mean()*100:+.2f} % (resto de meses {j.s[~q].mean()*100:+.2f} %)")

print("\n6) Monte Carlo 36 meses (dz_sim de los informes anteriores)")
src = open(os.path.join(AQUI, "dz_sim_base.py")).read().split("filas=[]")[0].replace("../dos-orb/serie_v018_be.csv", os.path.join(AQUI, "serie_v018_be.csv"))
b = {}; exec(src, b)
for nom, mm, cuota in [("ORB solo, cuenta CFD (35 €/mes)", j.o.values, 35.0), ("ORB solo, cuenta futuros (50 €/mes)", j.o.values, 50.0),
                       ("ORB + P, cuenta futuros (50 €/mes)", mix.values, 50.0),
                       ("ORB + P prima a la mitad, futuros (50 €/mes)", mixh.values, 50.0)]:
    for perm in (None, "obj10"):
        out, al, rd = b["sim"](mm, esc=0.45, perm=perm, cuota=cuota)
        print(f"  {nom:46s} perm {perm or 'no':5s} DARWIN/año {np.median(rd)*100:5.1f} %  asign. {al.mean():4.1f}  "
              f"neto €/año {out.mean()/3:6.0f}  mediana 36 m {np.median(out):6.0f}  P(neg) {(out<0).mean()*100:4.1f} %")

print("\nTamaño en la cuenta de futuros (1 M$): contratos de la pata P a 10 % de vol con los precios y pesos del último mes")
ult = wP.dropna().iloc[-1]; nominal = {"ES": 50 * es.iloc[-1], "ZN": 1000 * zn.iloc[-1], "GC": 100 * gc.iloc[-1]}
for c in ult.index: print(f"  {c}: peso {ult[c]:.2f} × 1 M$ = {ult[c]*1e6:,.0f} $ → {ult[c]*1e6/nominal[c]:.1f} contratos (1 contrato {nominal[c]:,.0f} $)")

print("\nSensibilidad (informativa): pata P con el sustituto al contado en todos los días (sin limpiar rolls)")
pz = (-6.5 * dy + carry).reindex(dias); pg = (xau.pct_change() - rf.reindex(xau.index)).reindex(dias)
pe = (spx.pct_change() - (rf.reindex(spx.index) - 0.018 / 252)).reindex(dias)
Ps, _ = pata({"ES": pe, "ZN": pz, "GC": pg}, {"acc": ["ES"], "bon": ["ZN"], "oro": ["GC"]})
sm = Ps.resample("ME").sum(); x = sm["2018":"2026-10"]
print(f"  pata 2018-26 SR {sr(x):.2f}; 2003-26 SR {sr(sm['2003':'2026-10']):.2f}")
js, ws, mxs = mezcla(o, sm); fila("ORB solo", js.o); fila("ORB + P (sustituto)", mxs)
print(f"\nReferencia: SR del ORB 2018-26 con Rbe sin coste {sr(orb.Rbe.resample('ME').sum()['2018':'2026-10']):.2f}; con R − 0,05 {sr((orb.R-0.05).resample('ME').sum()['2018':'2026-10']):.2f}")
