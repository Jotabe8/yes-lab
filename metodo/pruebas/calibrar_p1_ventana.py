"""Potencia de P1 según la ventana (2018-22 vs 2011-22). Uso: PYTHONPATH=. python metodo/pruebas/calibrar_p1_ventana.py"""
import numpy as np, pandas as pd
from statistics import NormalDist
import metodo.pruebas.calibrar_plantadas as C
from metodo.embudo import t_agrupado
def p1(o, desde):
    v=o[(o.fecha>=desde)&(o.fecha<"2023-01-01")]; n=(v.r_bruto-v.coste_r).to_numpy()
    return v.r_bruto.mean()>=3*C.COSTE and t_agrupado(n, v.fecha.dt.to_period("W").astype(str).to_numpy())>=1.645
for mu in (0.0,0.05,0.10,0.20):
  for f in (40,80,250):
    a=b=0
    for s in range(300):
        o=C.serie(mu,f,1,0.0,7000+s)
        a+=p1(o,"2018-01-01"); b+=p1(o,"2011-01-01")
    print(f"{mu:.2f} {f:4d}  P1 2018-22 {a/300:.2f}  P1 2011-22 {b/300:.2f}")
