# Prueba única 2023-2026 de la adenda del preregistro (cuenta sin swap, mercados de contado).
import numpy as np, pandas as pd
import tendencia as T
from tendencia import preparar, correr, periodo, t_stat
M = preparar()
M = {s: m for s, m in M.items() if m["g"] in ("indices", "forex", "metales") and s not in ("COPPER",)} | \
    {s: m for s, m in M.items() if s == "COPPER"}
for s, m in M.items():
    n = len(m["d"]); m["fins"]["sinswap"] = (np.zeros(n), np.zeros(n))
rng = np.random.default_rng(9)
filas = []
for sl in (True, False):
    for esc in ("sinswap", "normal", "ftmo"):
        ops, _ = correr(M, 100, 4.0, sl, esc)
        for a, b, nom in [("2005-01-01", "2022-12-31", "ajuste"), ("2023-01-01", "2026-12-31", "prueba")]:
            o = periodo(ops, a, b)
            fila = dict(lados="largos" if sl else "ambos", costes=esc, periodo=nom, ops=len(o), dias=o.dias.mean(),
                        neto=o.r_neto.mean(), t=t_stat(o.r_neto),
                        **{g: o[o.grupo == g].r_neto.mean() for g in ("indices", "forex", "metales")})
            if esc == "sinswap":
                nent = ops.groupby("mercado").size().reindex(list(M), fill_value=0).to_dict()
                pb = [periodo(correr(M, 100, 4.0, sl, esc, placebo_rng=rng, nent=nent)[0], a, b).r_neto.mean()
                      for _ in range(100)]
                fila.update(placebo=np.mean(pb), placebo_p95=np.percentile(pb, 95))
            filas.append(fila)
R = pd.DataFrame(filas)
pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False)); R.to_csv("oos_sin_swap.csv", index=False)
