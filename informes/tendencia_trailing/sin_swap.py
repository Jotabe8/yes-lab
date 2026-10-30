# ¿Qué queda de la tendencia si la cuenta no paga swap? (cuenta swap-free). Ajuste 2005-2022.
import numpy as np, pandas as pd
import tendencia as T
T.RECARGO["sinswap"] = {g: 0.0 for g in T.RECARGO["normal"]}
from tendencia import preparar, correr, periodo, t_stat, INI, FIN_AJUSTE
M = preparar()
for s, m in M.items():   # financiación cero en los dos lados
    n = len(m["d"]); m["fins"]["sinswap"] = (np.zeros(n), np.zeros(n))
rng = np.random.default_rng(3)
for N, TR, sl in [(55, 3.0, False), (100, 4.0, False), (55, 3.0, True), (100, 4.0, True)]:
    ops, _ = correr(M, N, TR, sl, "sinswap")
    o = periodo(ops, INI, FIN_AJUSTE); o = o[o.grupo != "cripto"]
    nent = ops.groupby("mercado").size().reindex(list(M), fill_value=0).to_dict()
    pb = []
    for k in range(100):
        p, _ = correr(M, N, TR, sl, "sinswap", placebo_rng=rng, nent=nent)
        p = periodo(p, INI, FIN_AJUSTE); pb.append(p[p.grupo != "cripto"].r_neto.mean())
    g = o.groupby("grupo").r_neto.mean().round(3).to_dict()
    print(f"{N}/{TR}/{'largos' if sl else 'ambos'} sin cripto: ops {len(o)} neto {o.r_neto.mean():+.3f} t {t_stat(o.r_neto):.2f} "
          f"| placebo neto medio {np.mean(pb):+.3f} p95 {np.percentile(pb,95):+.3f} | {g}")
