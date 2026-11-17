"""Calibración del embudo con ventajas PLANTADAS de tamaño conocido (17-11-2026).

Pregunta: ¿cuántas ventajas reales mata el embudo (potencia) y cuántas falsas deja pasar (falsos
positivos)? Se generan series de operaciones con forma de ORB (−1 R el 62 % de las veces, ganancias
exponenciales) y una ventaja neta conocida, y se pasan por el embudo tal cual (sin placebo, que
necesita la estrategia real). También 4 mercados correlacionados (rho 0,6 en el resultado del día)
para ver qué hace el t por operación frente al t por semana.

Uso: PYTHONPATH=. python metodo/pruebas/calibrar_plantadas.py [reps]
La EV del embudo se calcula aquí con 400 simulaciones (no 4000) para que quepa en minutos.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from statistics import NormalDist

import numpy as np
import pandas as pd

import metodo.embudo as E

DIAS = pd.bdate_range("2011-01-03", "2026-10-30")
COSTE = 0.03
P_PIERDE = 0.62
_ftmo = E.ftmo_2step


def _ftmo_rapido(*a, **k):
    k["n"] = 400
    return _ftmo(*a, **k)


E.ftmo_2step = _ftmo_rapido


def serie(mu_neto: float, ops_año: int, mercados: int, rho: float, semilla: int) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    años = len(DIAS) / 252
    n_dias = min(len(DIAS), int(round(ops_año * años / mercados)))
    idx = np.sort(rng.choice(len(DIAS), n_dias, replace=False))
    bruto = mu_neto + COSTE
    k = (bruto + P_PIERDE) / (1 - P_PIERDE)          # media de la ganancia para que E[R] = bruto
    z0 = rng.standard_normal(n_dias)
    filas = []
    for _ in range(mercados):
        z = np.sqrt(rho) * z0 + np.sqrt(1 - rho) * rng.standard_normal(n_dias)
        u = np.array([NormalDist().cdf(x) for x in z])
        r = np.where(u < P_PIERDE, -1.0, rng.exponential(k, n_dias))
        filas.append(pd.DataFrame({"fecha": DIAS[idx], "r_bruto": r, "coste_r": COSTE}))
    return pd.concat(filas, ignore_index=True)


def p1_rapido(o: pd.DataFrame, agrupar) -> bool:
    """P1 de METODO.md con 5 años (2018-22): bruto ≥ 3× coste y t ≥ 1,64 (sustituye al placebo p95)."""
    v = o[(o.fecha >= "2018-01-01") & (o.fecha < "2023-01-01")]
    if len(v) < 30:
        return False
    neto = (v.r_bruto - v.coste_r).to_numpy()
    g = v.fecha.dt.to_period(agrupar).astype(str).to_numpy() if agrupar else np.arange(len(v))
    return v.r_bruto.mean() >= 3 * COSTE and E.t_agrupado(neto, g) >= NormalDist().inv_cdf(0.95)


def celda(args):
    mu, f, m, rho, reps = args
    out = {"pasa_W": 0, "pasa_op": 0, "p1_W": 0, "p1_op": 0}
    for s in range(reps):
        o = serie(mu, f, m, rho, 1000 * s + int(mu * 1000) + f + m)
        out["pasa_W"] += E.embudo(o, 10, "2023-01-01", agrupar="W").pasa
        out["pasa_op"] += E.embudo(o, 10, "2023-01-01", agrupar=None).pasa if m > 1 else 0
        out["p1_W"] += p1_rapido(o, "W")
        out["p1_op"] += p1_rapido(o, None) if m > 1 else 0
    return {"R neta": mu, "ops/año": f, "mercados": m, **{k: v / reps for k, v in out.items()}}


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    rejilla = [(mu, f, 1, 0.0, reps) for mu in (0.0, 0.05, 0.10, 0.20) for f in (40, 80, 250)]
    rejilla += [(mu, f, 4, 0.6, reps) for mu in (0.0, 0.10) for f in (80, 250)]
    with Pool() as p:
        filas = p.map(celda, rejilla)
    t = pd.DataFrame(filas)
    pd.set_option("display.width", 140)
    print(f"Ventajas plantadas, {reps} réplicas por celda, 2011-26, corte OOS 2023, n_pruebas 10, coste {COSTE} R")
    print("pasa_W / pasa_op: embudo completo con t por semana / por operación")
    print("p1_W / p1_op: solo P1 rápido 2018-22 (bruto ≥ 3× coste y t ≥ 1,64)")
    print("Con R neta 0 las columnas son FALSOS POSITIVOS; con R > 0, POTENCIA.\n")
    print(t.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
