"""Junta metodo/revision2/paseo/*.csv.gz (salida de paseo_orb.py en GitHub) y aplica la lectura del preregistro."""
import glob, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from metodo.sinteticos import prueba_motor
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paseo")
COSTE_PCT = {"GER40": 0.000052, "JP225": 0.000157}   # horquilla FTMO medida (v3/spread_aperturas_ftmo.csv)
x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{D}/*.csv.gz"))])
t = lambda v: v.mean() / v.std(ddof=1) * np.sqrt(len(v))
for sim, g in x.groupby("sim"):
    real = g[g.rep < 0]; pas = g[g.rep >= 0]
    coste = (COSTE_PCT[sim] / real.dist_pct).mean()
    pm = prueba_motor([pas.r.values], coste)
    pc = prueba_motor([pas.r_contra.values], coste)
    print(f"{sim}: real {real.fecha.min()}→{real.fecha.max()} {len(real)} ops, bruto {real.r.mean():+.3f} (t {t(real.r):.2f}), "
          f"neto {real.r.mean() - coste:+.3f} (t {t(real.r - coste):.2f}), coste {coste:.3f} R")
    print(f"   paseo regla:     {pm['detalle']} -> {'pasa' if pm['pasa'] else 'NO PASA'}")
    print(f"   paseo contraria: {pc['detalle']} -> {'pasa' if pc['pasa'] else 'NO PASA'}")
    print("   paseo por año:", pas.groupby(pd.to_datetime(pas.fecha).dt.year).r.mean().round(3).to_dict())
