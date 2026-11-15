"""P1: el mismo backtest del ORB v018/v019 sobre velas de paseo aleatorio (20 réplicas). Debe dar R bruta ≈ 0."""
import sys
import numpy as np
import pandas as pd
from metodo.sinteticos import velas_paseo, prueba_motor
from metodo.pruebas.orb_v019.replica import simular

v = pd.read_pickle(sys.argv[1]).loc["2021-09-01":]          # solo la parte M1 del CSV de FTMO
casos = {"v019 cuenta (= v018)": dict(), "v019 tope de pausa 21 d": dict(tope_pausa=21),
         "sin filtro de volatilidad": dict(filtro_vol=False)}
brutas = {k: [] for k in casos}
netas = {k: [] for k in casos}
for s in range(20):
    p = velas_paseo(v, s)
    for k, kw in casos.items():
        brutas[k].append(simular(p, coste=False, **kw).r.to_numpy())
        netas[k].append(simular(p, coste=True, **kw).r.to_numpy())
    print("semilla", s, "hecha", flush=True)
real = simular(v, coste=False)
print(f"\nDatos reales 2021-09/2026-10 (mismo código, sin coste): {len(real)} ops, R bruta {real.r.mean():+.3f}")
for k in casos:
    rb = np.concatenate(brutas[k]); rn = np.concatenate(netas[k])
    coste = rb.mean() - rn.mean()
    pm = prueba_motor(brutas[k], coste_r=coste)
    print(f"{k}: {pm['detalle']}; con spread {rn.mean():+.3f} (coste {coste:.3f} R/op); "
          f"stops 1 R exactos o peores {np.mean(rb <= -0.999):.0%}; PASA={pm['pasa']}")
