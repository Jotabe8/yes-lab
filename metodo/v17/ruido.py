"""v17 ronda 3: prueba de ruido (Build Alpha / StrategyQuant "noise test") sobre la cohorte.

Las SEÑALES se recalculan sobre OHLC con ruido (σ = 0,15 ATR por precio, H/L reajustados) y la R se mide
sobre los precios reales. Rasgo: t medio de ajuste con ruido (8 réplicas). Si el ruido sirve, ese t debe
predecir el fuera de muestra mejor que el t sin ruido. Salida: metodo/v17/ruido.csv.gz
"""
from __future__ import annotations
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
from metodo.v17.cohorte import CLASES, COSTE_LADO, carga, metricas, reglas

SIGMA, REPS, CORTE = 0.15, 8, "2015-01-01"


def con_ruido(d, rng):
    x = d.copy()
    a = d.ATR.to_numpy()
    for c in ("Open", "High", "Low", "Close"):
        x[c] = d[c].to_numpy() + rng.standard_normal(len(d)) * SIGMA * a
    x["High"] = x[["Open", "High", "Low", "Close"]].max(axis=1)
    x["Low"] = x[["Open", "High", "Low", "Close"]].min(axis=1)
    return x


def mercado(m):
    d = carga(m)
    msk = (d.index >= "2001-01-01") & (d.index < CORTE)
    if msk.sum() < 200:
        return []
    ret = d.ret.to_numpy()
    rng = np.random.default_rng(abs(hash(m)) % 2**32)
    acum = {}
    for _ in range(REPS):
        for fam, par, lado, pos in reglas(con_ruido(d, rng)):
            pos = np.nan_to_num(pos)
            cambio = np.abs(np.diff(np.r_[0.0, pos]))
            rx = pos[msk] * (ret[msk] - ret[msk].mean()) - COSTE_LADO * cambio[msk]
            r = pos[msk] * ret[msk] - COSTE_LADO * cambio[msk]
            k = (m, fam, par[0], par[1], lado)
            acum.setdefault(k, []).append((metricas(rx, d.index[msk])[1], metricas(r, d.index[msk])[1]))
    return [dict(mercado=k[0], familia=k[1], p1=k[2], p2=k[3], lado=k[4],
                 tx_ruido=np.mean([a for a, _ in v]), t_ruido=np.mean([b for _, b in v])) for k, v in acum.items()]


if __name__ == "__main__":
    ms = [m for v in CLASES.values() for m in v]
    with Pool(3) as p:
        filas = [f for r in p.map(mercado, ms) for f in r]
    pd.DataFrame(filas).to_csv(Path(__file__).parent / "ruido.csv.gz", index=False)
    print(len(filas))
