"""Seguimiento en real v14c (PREREGISTRO_SEGUIMIENTO.md). Uso: seguimiento.py ruta/ops_live.csv"""
import sys, glob, os
import numpy as np, pandas as pd
D = os.path.dirname(os.path.abspath(__file__))
INICIO = pd.Timestamp("2026-11-17")
ops = pd.read_csv(sys.argv[1], sep=";")
ops = ops[ops.Simbolo.str.startswith("US100") & ops.ea.str.contains("ORB_US100")].copy()
ops["fecha"] = pd.to_datetime(ops.Fecha, format="%Y.%m.%d")
fr = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/datos/US100_*.csv")])
fr["fecha"] = pd.to_datetime(fr.fecha); fr = fr.sort_values("fecha").drop_duplicates("fecha")
for c in ["h5", "hhoy"]:
    fr[f"med_{c}"] = fr[c].shift(1).rolling(250, min_periods=60).median()
j = ops.merge(fr, on="fecha", how="left")
def resumen(x, nom):
    print(f"\n== {nom}: {len(x)} operaciones ({x.fecha.min():%d-%m-%Y} a {x.fecha.max():%d-%m-%Y}) ==" if len(x) else f"\n== {nom}: 0 operaciones ==")
    for c in ["h5", "hhoy"]:
        y = x[x[c].notna() & x[f"med_{c}"].notna()]
        sin = len(x) - len(y)
        pe, an = y[y[c] >= y[f"med_{c}"]].R, y[y[c] < y[f"med_{c}"]].R
        if len(pe) < 2 or len(an) < 2:
            print(f"  {c}: persistentes {len(pe)}, antipersistentes {len(an)}, sin régimen aún {sin} (pocos datos)"); continue
        dif = pe.mean() - an.mean(); se = np.sqrt(pe.var(ddof=1) / len(pe) + an.var(ddof=1) / len(an))
        print(f"  {c}{' (DECIDE)' if c == 'h5' else ''}: persistente {pe.mean():+.3f} R (n {len(pe)}) | antipersistente {an.mean():+.3f} R (n {len(an)}) | dif {dif:+.3f} t {dif/se:.2f} | sin régimen {sin}")
    if nom.startswith("Decisión"):
        n = len(x); print(f"  Estado: {n}/100 operaciones." + (" DECIDIR ya (dif > 0 y t ≥ 1,65)." if n >= 100 else " Aún no se decide."))
resumen(j[j.fecha < INICIO], "Antes del preregistro (no cuenta)")
resumen(j[j.fecha >= INICIO], "Decisión (desde 17-11-2026)")
