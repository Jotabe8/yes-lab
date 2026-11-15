"""Pruebas del PREREGISTRO_BONOS.md. Uso: python darwinex/bonos_dz.py datos_bonos"""
import sys, os, re, numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "datos_bonos"
DUR = {2: 1.9, 5: 4.6, 7: 6.3, 10: 8.5, 30: 17.0}
def fred(s):
    d = pd.read_csv(os.path.join(D, s + ".csv")); d.columns = ["d", "v"]
    return pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()
Y = pd.DataFrame({k: fred(f"DGS{k}") for k in DUR}).dropna(how="all").ffill()
Y = Y[Y.index >= "1988-01-01"]
R = pd.DataFrame({k: -DUR[k] * Y[k].diff() / 100 + Y[k].shift(1) / 100 / 252 for k in DUR})   # retorno del bono
R[3] = (R[2] + R[5]) / 2; R[20] = (R[10] + R[30]) / 2
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
def linea(nom, x, coste=0.0):
    x = pd.Series(x).dropna(); n = x - coste; h = len(n) // 2
    print(f"{nom:52s} n {len(x):4d} | bruto {x.mean():6.2f} pb (t {t(x):5.2f}) | neto {n.mean():6.2f} (t {t(n):5.2f})"
          f" | 1ª mitad {n.iloc[:h].mean():6.2f} 2ª {n.iloc[h:].mean():6.2f} | costes x2 {(x-2*coste).mean():6.2f}")
# ---------------- Idea 1: ciclo de subastas
A = pd.read_csv(os.path.join(D, "subastas.csv"))
A = A[A.security_type.isin(["Note", "Bond"])].copy()
def plazo(s):
    m = re.match(r"(\d+)-Year(?:\s+(\d+)-Month)?", str(s))
    if not m: return np.nan
    a = int(m.group(1)) + (int(m.group(2)) / 12 if m.group(2) else 0)
    return min([2, 3, 5, 7, 10, 20, 30], key=lambda k: abs(k - a))
A["k"] = A.security_term.map(plazo); A["fecha"] = pd.to_datetime(A.auction_date)
A = A.dropna(subset=["k"]).drop_duplicates(["fecha", "k"])
idx = R.index
vol = {k: R[k].rolling(250, min_periods=120).std().shift(1) for k in R.columns}
def ciclos(desfase=0):
    filas = []
    for _, a in A.iterrows():
        i = idx.searchsorted(a["fecha"]) + desfase
        if i < 260 or i + 5 >= len(idx): continue
        k = int(a.k); r = R[k].values
        pre, post = r[i - 5:i].sum(), r[i:i + 5].sum()
        esc = vol[5].iloc[i] / vol[k].iloc[i]                      # a riesgo del 5 años
        filas.append(dict(T=idx[i], k=k, c=(post - pre) * 1e4 * esc))
    f = pd.DataFrame(filas); f["sem"] = f["T"].dt.to_period("W")
    s = f.groupby("sem").agg(T=("T", "min"), c=("c", "mean")).set_index("T").c
    return f, s
f, s = ciclos(); fp, sp = ciclos(10)
print("IDEA 1: CICLO DE SUBASTAS (pb a riesgo del 5 años; coste 3 pb)")
for nom, a, b in [("2009-2026 (principal, fuera de la muestra publicada)", "2009", "2026"), ("1990-2008 (réplica del artículo)", "1990", "2008")]:
    linea(nom, s[a:b], 3.0); linea("   placebo dos semanas después", sp[a:b], 3.0)
print("Por plazo, 2009-2026 (cada subasta):")
for k in sorted(f.k.unique()):
    linea(f"   {k} años", f[(f.k == k) & (f["T"] >= "2009")].c, 3.0)
print("Por año, 2009-2026, media neta pb:", s["2009":].sub(3).groupby(s["2009":].index.year).mean().round(1).to_dict())
# ---------------- Idea 2: rebalanceo de pensiones
g = pd.read_csv(os.path.join(D, "GSPC.csv"), index_col=0, parse_dates=True)["Close"].astype(float)
E = g.pct_change(); B = R[10]
J = pd.concat([E, B], axis=1, keys=["e", "b"], sort=True).dropna()
J = J[J.index >= "1999-01-01"]
ve, vb = J.e.rolling(60).std().shift(1), J.b.rolling(60).std().shift(1)
def rebal(dia_senal):
    filas = []
    for _, g2 in J.groupby(J.index.to_period("M")):
        n = len(g2)
        if n < 15: continue
        s_ = n - 1 - 5 if dia_senal == "fin" else 9          # índice del día de la señal dentro del mes
        fin = n - 1 if dia_senal == "fin" else s_ + 4         # hasta el penúltimo día hábil (o 4 días)
        d0 = g2.index[s_]
        mtd = (1 + g2.e.iloc[:s_ + 1]).prod() - (1 + g2.b.iloc[:s_ + 1]).prod()
        p = -np.sign(mtd)
        w_e, w_b = 0.5, 0.5 * ve.loc[d0] / vb.loc[d0]
        r = (g2.e.iloc[s_ + 1:fin] * w_e - g2.b.iloc[s_ + 1:fin] * w_b).sum()
        filas.append(dict(d=d0, r=p * r * 1e4))
    return pd.DataFrame(filas).set_index("d").r
x, xp = rebal("fin"), rebal("medio")
print("\nIDEA 2: REBALANCEO DE PENSIONES A FIN DE MES (pb; coste 3 pb)")
linea("1999-2026 (principal)", x, 3.0); linea("   placebo mitad de mes", xp, 3.0)
linea("2023-04 → 2026-10 (fuera de la muestra publicada)", x["2023-04":], 3.0)
linea("Trimestres (3.er mes)", x[x.index.month % 3 == 0], 3.0)
print("Sharpe anual neto:", round((x - 3).mean() / (x - 3).std() * np.sqrt(12), 2))
