"""Informativo (no estaba en el preregistro): ¿se ve el ciclo de subastas en los FUTUROS (lo que se operaría)?
Futuros continuos de Yahoo (ZT 2 a, ZF 5 a, ZN 10 a, ZB 30 a). Para evitar los saltos de vencimiento se quitan
los ciclos cuya ventana toca del día 20 al final de febrero, mayo, agosto y noviembre. Se compara con FRED en
el mismo subconjunto. 2009-2026."""
import sys, os, re, numpy as np, pandas as pd
exec(open("darwinex/bonos_dz.py").read().split("# ---------------- Idea 2")[0].replace("sys.argv[1] if len(sys.argv) > 1 else \"datos_bonos\"", "\"datos_bonos\""))
FUT = {2: "ZT", 5: "ZF", 10: "ZN", 30: "ZB"}
F = pd.DataFrame({k: pd.read_csv(f"datos_bonos/{v}.csv", index_col=0, parse_dates=True)["Close"].astype(float).pct_change() for k, v in FUT.items()})
F = F.reindex(idx)
def roll(d): return d.month in (2, 5, 8, 11) and d.day >= 20
res = {"FRED": [], "futuro": []}
for _, a in A.iterrows():
    k = int(a.k)
    if k not in FUT or a["fecha"] < pd.Timestamp("2009-01-01"): continue
    i = idx.searchsorted(a["fecha"])
    if i + 5 >= len(idx): continue
    ventana = idx[i - 6:i + 5]
    if any(roll(d) for d in ventana): continue
    for nom, X in (("FRED", R), ("futuro", F)):
        r = X[k].values; c = (r[i:i + 5].sum() - r[i - 5:i].sum())
        if np.isnan(c): continue
        res[nom].append(dict(k=k, c=c * 1e4 * vol[5].iloc[i] / vol[k].iloc[i]))
for nom, l in res.items():
    d = pd.DataFrame(l)
    for k in FUT: linea(f"{nom} {k} años (sin días de roll)", d[d.k == k].c, 3.0)
    linea(f"{nom} todos", d.c, 3.0)
