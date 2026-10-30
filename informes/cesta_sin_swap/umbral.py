# Mismo Monte Carlo, esperando a acumular más beneficio antes del primer retiro.
import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
src = open("cesta_e8.py").read().split("filas = []")[0]
src = src.replace("if eq - ultimo >= 0.01 * CAP:", "if eq - ultimo >= (U1 if pagos == 0 else U2) * CAP:")
res = []
for U1 in (0.01, 0.04, 0.08, 0.12):
    for U2 in (0.01, 0.03):
        g = {"U1": U1, "U2": U2, "__file__": __file__}; exec(src, g)
        for v in (0.05, 0.075, 0.10):
            r = g["serie"](v)
            p, c, m = g["mc"](r, n=2000); p0, c0, _ = g["mc"](r - r.mean(), n=2000)
            res.append(dict(primer_retiro=U1, siguientes=U2, vol=v, p_pasa=p, cobro=c, control=c0))
T = pd.DataFrame(res); print(T.round(3).to_string(index=False)); T.to_csv("ev_e8_umbral.csv", index=False)
