"""v17 ronda 5: ¿el PBO (CSCV), que el embudo usa como puerta que BLOQUEA (> 0,5), predice el fuera de muestra
de la variante elegida? Grupos mercado×familia×lado con ≥ 6 variantes de rejilla; PBO sobre la matriz diaria de
ajuste (R sin deriva), 10 bloques. Objetivo: t fuera (sin deriva) de la mejor variante del ajuste."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
from metodo.robustez import pbo
from metodo.v17.cohorte import CLASES, COSTE_LADO, carga, metricas, reglas

CORTE = sys.argv[1] if len(sys.argv) > 1 else "2015-01-01"


def mercado(m):
    d = carga(m)
    ins = (d.index >= "2001-01-01") & (d.index < CORTE)
    oos = d.index >= CORTE
    if ins.sum() < 500:
        return []
    ret = d.ret.to_numpy()
    grupos = {}
    for fam, par, lado, pos in reglas(d):
        pos = np.nan_to_num(pos)
        cambio = np.abs(np.diff(np.r_[0.0, pos]))
        r_in = pos[ins] * (ret[ins] - ret[ins].mean()) - COSTE_LADO * cambio[ins]
        r_out = pos[oos] * (ret[oos] - ret[oos].mean()) - COSTE_LADO * cambio[oos]
        grupos.setdefault((fam, lado), []).append((par, r_in, r_out))
    out = []
    for (fam, lado), vs in grupos.items():
        if len(vs) < 6:
            continue
        M = np.column_stack([v[1] for v in vs])
        pb = pbo(M, s=10)
        t_in = np.array([metricas(v[1], d.index[ins])[1] for v in vs])
        t_out = np.array([metricas(v[2], d.index[oos])[1] for v in vs])
        b = int(np.argmax(t_in))
        out.append(dict(mercado=m, familia=fam, lado=lado, n_var=len(vs), pbo=pb["pbo"],
                        t_in_mejor=t_in[b], t_out_mejor=t_out[b], t_out_media=t_out.mean(),
                        t_in_media=t_in.mean()))
    return out


if __name__ == "__main__":
    ms = [m for v in CLASES.values() for m in v]
    with Pool(4) as p:
        f = pd.DataFrame([r for x in p.map(mercado, ms) for r in x])
    f.to_csv(Path(__file__).parent / f"ronda5_{CORTE[:4]}.csv", index=False)
    print(f"{len(f)} grupos; Spearman(PBO, t fuera de la elegida) {f.pbo.rank().corr(f.t_out_mejor.rank()):+.3f}; "
          f"Spearman(t ajuste de la elegida, t fuera) {f.t_in_mejor.rank().corr(f.t_out_mejor.rank()):+.3f}")
    f["clase_pbo"] = pd.cut(f.pbo, [-0.01, 0.2, 0.5, 1.0], labels=["≤0,2", "0,2-0,5", ">0,5 (bloquea)"])
    print(f.groupby("clase_pbo", observed=True).agg(n=("pbo", "size"), t_in=("t_in_mejor", "mean"),
          t_out=("t_out_mejor", "mean"), pos=("t_out_mejor", lambda v: (v > 0).mean()),
          t_out_gt1=("t_out_mejor", lambda v: (v > 1).mean())).round(2).to_string())
    # entre los que pasarían el resto (t ajuste de la elegida ≥ 2,58), ¿qué añade el PBO?
    g = f[f.t_in_mejor >= 2.58]
    print(f"\nCon t ajuste de la elegida ≥ 2,58: n {len(g)}")
    print(g.groupby("clase_pbo", observed=True).agg(n=("pbo", "size"), t_out=("t_out_mejor", "mean"),
          pos=("t_out_mejor", lambda v: (v > 0).mean())).round(2).to_string())
