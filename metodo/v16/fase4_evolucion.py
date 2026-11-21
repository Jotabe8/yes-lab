"""v16 fase 4 — ¿se puede «evolucionar» un sistema aleatorio hasta uno ganador?

Desde cada uno de los 5 sistemas aleatorios: 300 mutaciones (cambia hora, H, k o regla) con
ascenso de colina sobre el t neto 2018-20 (entrenamiento); se mira 2021-22 (validación) y 2023-26
(fuera). Mide cuánto de lo que encuentra la optimización es ajuste al ruido.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from metodo.embudo import t_agrupado
from metodo.v16.datos import MERCADOS, NOMBRE, SEMILLA, cargar
from metodo.v16.fase1_aleatorios import HS, REGLAS, direccion, sortear
from metodo.v16.motor import Mercado, horas_liquidas


def tramo(M, s, mk):
    R, c = M.operar(s['b'], s['H'], s['k'], direccion(M, s))
    sem = pd.to_datetime(M.dias.astype(str)).to_period('W').astype(str).to_numpy()
    ok = np.isfinite(R) & mk
    neto = R[ok] - c[ok]
    return (t_agrupado(neto, sem[ok]) if ok.sum() > 50 else -9), (neto.mean() if ok.sum() else np.nan)


def mutar(rng, s, liq):
    s = dict(s)
    q = rng.integers(4)
    if q == 0:
        s['b'] = int(np.clip(s['b'] + rng.choice([-12, -6, -1, 1, 6, 12]), 12, 287))
    elif q == 1:
        s['H'] = int(rng.choice(HS))
    elif q == 2:
        s['k'] = float(np.clip(round(s['k'] + rng.normal(0, 0.15), 2), 0.1, 2.0))
    else:
        s['regla'] = str(rng.choice(REGLAS))
    ok = (s['b'] in liq) and (s['b'] + s['H'] <= 288) and ((s['b'] + s['H'] - 1) in liq)
    return s if ok else None


if __name__ == '__main__':
    filas = []
    for i, m in enumerate(MERCADOS):
        M = Mercado(m, *cargar(m))
        liq = set(horas_liquidas(M).tolist())
        ent = M.dias <= 20201231
        val = (M.dias > 20201231) & (M.dias <= 20221231)
        oos = M.dias > 20221231
        s = sortear(np.random.default_rng(SEMILLA + i), M, np.array(sorted(liq)))
        t0 = tramo(M, s, ent)[0]
        rng = np.random.default_rng(SEMILLA + 100 + i)
        mejor, tm = s, t0
        for _ in range(300):
            c = mutar(rng, mejor, liq)
            if c is None:
                continue
            tc = tramo(M, c, ent)[0]
            if tc > tm:
                mejor, tm = c, tc
        tv, nv = tramo(M, mejor, val)
        to, no = tramo(M, mejor, oos)
        filas.append(dict(mercado=NOMBRE[m], t_inicial=round(t0, 2), regla_final=f"{mejor['b'] * 5 // 60:02d}:{mejor['b'] * 5 % 60:02d} H{mejor['H'] * 5}m k{mejor['k']} {mejor['regla']}",
                          t_entreno=round(tm, 2), t_valid=round(tv, 2), neto_valid=round(nv, 4),
                          t_oos=round(to, 2), neto_oos=round(no, 4)))
    pd.set_option('display.width', 250)
    print(pd.DataFrame(filas).to_string(index=False))
