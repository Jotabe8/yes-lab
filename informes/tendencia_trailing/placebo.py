# Placebo con las mismas salidas: entrada en día (y dirección) al azar, misma frecuencia por mercado.
import numpy as np, pandas as pd
from tendencia import preparar, correr, periodo, INI, FIN_AJUSTE
M = preparar()
filas = []
for N, TR, sl in [(55, 3.0, False), (55, 3.0, True), (100, 4.0, True), (20, 4.0, True)]:
    ops, _ = correr(M, N, TR, sl)
    o = periodo(ops, INI, FIN_AJUSTE)
    nent = ops.groupby("mercado").size().reindex(list(M), fill_value=0).to_dict()
    rng = np.random.default_rng(7)
    pb, pn, pg = [], [], {}
    for k in range(200):
        p, _ = correr(M, N, TR, sl, placebo_rng=rng, nent=nent)
        p = periodo(p, INI, FIN_AJUSTE)
        pb.append(p.r_bruto.mean()); pn.append(p.r_neto.mean())
        for g, v in p.groupby("grupo").r_bruto.mean().items(): pg.setdefault(g, []).append(v)
    pb = np.array(pb)
    fila = dict(N=N, TR=TR, lados="largos" if sl else "ambos", bruto=o.r_bruto.mean(), placebo_media=pb.mean(),
                placebo_p95=np.percentile(pb, 95), pct_placebo_mayor=(pb >= o.r_bruto.mean()).mean(),
                neto=o.r_neto.mean(), placebo_neto=np.mean(pn))
    filas.append(fila)
    g = o.groupby("grupo").r_bruto.agg(["count", "mean"])
    g["placebo"] = [np.mean(pg[x]) for x in g.index]; g["p95"] = [np.percentile(pg[x], 95) for x in g.index]
    print(f"\n{N}/{TR}/{fila['lados']} por grupo (bruto):\n", g.round(3).to_string())
T = pd.DataFrame(filas); print("\n", T.round(3).to_string(index=False)); T.to_csv("placebo_ajuste.csv", index=False)
