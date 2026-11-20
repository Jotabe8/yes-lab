"""Cuántas celdas pasarían la regla de selección (|t|≥4 y efecto ≥ 2× coste) en mapas nulos."""
import numpy as np
from metodo.v16.fase2_mapa import mapa, preparar
Ms, celdas = preparar()
c = []
for k in range(50):
    nu = mapa(Ms, celdas, rng=np.random.default_rng(1000 + k))
    c.append(int(((nu.t.abs() >= 4) & (nu.efecto_x_coste >= 2)).sum()))
print('nulo: celdas que pasan la selección por mapa: media', np.mean(c), 'p95', np.quantile(c, .95), 'reparto', np.bincount(c))
