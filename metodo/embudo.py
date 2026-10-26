"""Embudo de pruebas para cribar ideas de EA en minutos (ver metodo/METODO.md).

Entrada mínima: una serie de operaciones con su fecha de cierre y su resultado en R
(bruto, antes de costes) y el coste de ida y vuelta de cada operación en R.

    import pandas as pd
    from metodo.embudo import embudo
    ops = pd.DataFrame({"fecha": fechas, "r_bruto": r, "coste_r": coste})
    embudo(ops, n_pruebas=12, corte_oos="2023-01-01", placebo=lambda s: sim(seed=s))

`placebo(semilla)` debe devolver las R brutas de la misma estrategia con la dirección
(o la hora de entrada) aleatoria y las mismas salidas; si no se pasa, se omite esa puerta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np
import pandas as pd

# Umbrales de las puertas. Cambiarlos aquí, nunca a mitad de una prueba.
MIN_OPS_AÑO = 40          # menos operaciones no sirven para pasar un reto en semanas
MAX_COSTE_R = 0.10        # coste medio por operación en R
MIN_BRUTO_VS_COSTE = 3.0  # el bruto debe ser al menos 3 veces el coste
MIN_AÑOS_POSITIVOS = 0.6  # fracción de años con neto > 0
MIN_DOBLE_COSTE = 0.0     # neto con costes al doble debe seguir > 0


def t_stat(r: np.ndarray) -> float:
    r = np.asarray(r, float)
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r)))


def t_requerido(n_pruebas: int, alfa: float = 0.05) -> float:
    """t mínimo (una cola) tras corregir por el número de variantes probadas (Bonferroni).

    1 prueba → 1,64; 10 → 2,58; 100 → 3,29; 1.000 → 3,89. Contar TODAS las variantes
    miradas (parámetros, mercados, horarios), no solo la que se presenta.
    """
    return NormalDist().inv_cdf(1 - alfa / max(1, n_pruebas))


def drawdown_max(r: np.ndarray) -> float:
    eq = np.cumsum(r)
    return float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq, initial=0.0))


def montecarlo_dd(r: np.ndarray, n: int = 5000, semilla: int = 0) -> dict:
    """Remuestrea el orden de las operaciones; devuelve percentiles del DD máximo en R."""
    rng = np.random.default_rng(semilla)
    r = np.asarray(r, float)
    dds = np.array([drawdown_max(rng.permutation(r)) for _ in range(n)])
    return {"dd_p50": float(np.percentile(dds, 50)), "dd_p95": float(np.percentile(dds, 95))}


def ruido(r: np.ndarray, n: int = 1000, sd_r: float = 0.1, semilla: int = 0) -> float:
    """Prueba de ruido barata: suma ruido N(0, sd_r) a cada operación y tira el 10 % de
    ellas al azar. Devuelve la fracción de réplicas con media > 0. Para una prueba de
    ruido completa hay que perturbar los precios y volver a simular (ver METODO.md)."""
    rng = np.random.default_rng(semilla)
    r = np.asarray(r, float)
    buenas = 0
    for _ in range(n):
        m = rng.random(len(r)) > 0.10
        buenas += (r[m] + rng.normal(0, sd_r, m.sum())).mean() > 0
    return buenas / n


def ftmo_2step(r_dia: np.ndarray, riesgo: float = 0.01, cuota: float = 540.0,
               capital: float = 100_000, meses_fondeada: int = 12, reparto: float = 0.8,
               n: int = 4000, semilla: int = 0) -> dict:
    """EV aproximado por cuota de un 2-Step FTMO remuestreando DÍAS de R (no operaciones).

    Reto: +10 %, verificación: +5 %, sin límite de tiempo, pérdida diaria 5 % y total 10 %
    estáticas. Fondeada: retiro mensual del beneficio por encima del inicial, 80 %, cuota
    devuelta con el primer retiro. Es una criba rápida: el simulador de referencia es
    cartera/equilibrio.py en el PC de Jorge.
    """
    rng = np.random.default_rng(semilla)
    r_dia = np.asarray(r_dia, float)
    pasa, cobros = 0, np.zeros(n)
    for i in range(n):
        ok = True
        for objetivo in (0.10, 0.05):
            eq, dias = 0.0, 0
            while True:
                d = rng.choice(r_dia) * riesgo
                dias += 1
                if d <= -0.05 or eq + d <= -0.10 or dias > 750:
                    ok = False
                    break
                eq += d
                if eq >= objetivo and dias >= 4:
                    break
            if not ok:
                break
        if not ok:
            continue
        pasa += 1
        eq, total, devuelta = 0.0, 0.0, False
        for _ in range(meses_fondeada):
            quemada = False
            for _ in range(21):
                d = rng.choice(r_dia) * riesgo
                if d <= -0.05 or eq + d <= -0.10:
                    quemada = True
                    break
                eq += d
            if quemada:
                break
            if eq > 0:
                total += eq * capital * reparto + (0 if devuelta else cuota)
                devuelta, eq = True, 0.0
        cobros[i] = total
    return {"p_pasar": pasa / n, "ev_cuota": float(cobros.mean() - cuota)}


@dataclass
class Resultado:
    puertas: list = field(default_factory=list)  # (nombre, ok, detalle)

    def add(self, nombre, ok, detalle):
        self.puertas.append((nombre, bool(ok), detalle))

    @property
    def pasa(self):
        return all(ok for _, ok, _ in self.puertas)

    def __str__(self):
        filas = [f"{'OK ' if ok else 'NO '} {n:<28} {d}" for n, ok, d in self.puertas]
        filas.append("VEREDICTO: " + ("sigue al siguiente paso" if self.pasa else "DESCARTAR"))
        return "\n".join(filas)


def embudo(ops: pd.DataFrame, n_pruebas: int, corte_oos: str, placebo=None,
           n_placebo: int = 200, riesgo: float = 0.01, cuota: float = 540.0,
           ev_control: float | None = None) -> Resultado:
    """Aplica las puertas P1-P5 de METODO.md y devuelve el veredicto.

    ops: columnas fecha (datetime), r_bruto (R antes de costes), coste_r (R por operación).
    ev_control: EV/cuota del control sin edge (p. ej. la cesta de índices); si se pasa, la
    idea tiene que superarlo.
    """
    ops = ops.sort_values("fecha").reset_index(drop=True)
    ops["fecha"] = pd.to_datetime(ops["fecha"])
    neto = (ops.r_bruto - ops.coste_r).to_numpy()
    neto2 = (ops.r_bruto - 2 * ops.coste_r).to_numpy()
    años = (ops.fecha.iloc[-1] - ops.fecha.iloc[0]).days / 365.25 or 1
    res = Resultado()

    # P0-P1: frecuencia y coste
    ops_año = len(ops) / años
    res.add("frecuencia", ops_año >= MIN_OPS_AÑO, f"{ops_año:.0f} ops/año (mín {MIN_OPS_AÑO})")
    coste = ops.coste_r.mean()
    bruto = ops.r_bruto.mean()
    res.add("coste en R", coste <= MAX_COSTE_R, f"{coste:.3f} R/op (máx {MAX_COSTE_R})")
    res.add("bruto vs coste", bruto >= MIN_BRUTO_VS_COSTE * coste,
            f"bruto {bruto:+.3f} R = {bruto / coste if coste else np.inf:.1f}× coste")

    # P1: placebo con las mismas salidas
    if placebo is not None:
        medias = np.array([np.mean(placebo(s)) for s in range(n_placebo)])
        p95 = float(np.percentile(medias, 95))
        res.add("supera placebo p95", bruto > p95, f"bruto {bruto:+.3f} vs p95 {p95:+.3f}")

    # P2: neto, costes al doble, estabilidad por años, ruido
    dentro = ops.fecha < pd.Timestamp(corte_oos)
    res.add("neto ajuste > 0", neto[dentro].mean() > 0,
            f"{neto[dentro].mean():+.3f} R/op, t {t_stat(neto[dentro]):.2f}")
    res.add("coste ×2 > 0", neto2.mean() > MIN_DOBLE_COSTE, f"{neto2.mean():+.3f} R/op")
    por_año = pd.Series(neto).groupby(ops.fecha.dt.year).sum()
    frac = (por_año > 0).mean()
    res.add("años positivos", frac >= MIN_AÑOS_POSITIVOS,
            f"{(por_año > 0).sum()}/{len(por_año)} años")
    fr = ruido(neto)
    res.add("ruido", fr >= 0.9, f"{fr:.0%} réplicas con media > 0")

    # P3: fuera de muestra con t corregido por número de pruebas
    oos = neto[~dentro]
    t_req = t_requerido(n_pruebas)
    res.add("fuera de muestra", len(oos) > 30 and oos.mean() > 0 and t_stat(oos) >= 1.0,
            f"{oos.mean() if len(oos) else 0:+.3f} R/op, n {len(oos)}, t {t_stat(oos):.2f}")
    res.add("t total corregido", t_stat(neto) >= t_req,
            f"t {t_stat(neto):.2f} vs {t_req:.2f} ({n_pruebas} pruebas)")

    # P5: Monte Carlo y EV por cuota
    mc = montecarlo_dd(neto)
    r_dia = pd.Series(neto).groupby(ops.fecha.dt.date).sum().to_numpy()
    ev = ftmo_2step(r_dia, riesgo=riesgo, cuota=cuota)
    umbral = ev_control if ev_control is not None else 0.0
    res.add("EV/cuota 2-Step", ev["ev_cuota"] > umbral,
            f"{ev['ev_cuota']:+.0f} € (p pasar {ev['p_pasar']:.0%}, umbral {umbral:+.0f}),"
            f" DD p95 {mc['dd_p95']:.1f} R")
    return res
