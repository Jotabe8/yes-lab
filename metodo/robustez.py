"""Pruebas contra el sobreajuste para el embudo (P2-P3 y P6 de METODO.md).

- spa(): Superior Predictive Ability de Hansen (versión mejorada del White Reality Check)
  y StepM de Romano-Wolf, con bootstrap estacionario por bloques (librería `arch`).
  Responde a "¿la mejor de mis N variantes bate a no operar, sabiendo que miré N?" usando
  la correlación real entre variantes, en vez de suponerlas independientes (Bonferroni).
- pbo(): Probability of Backtest Overfitting por CSCV (Bailey, Borwein, López de Prado y Zhu
  2015): con qué frecuencia la mejor variante dentro de muestra queda por debajo de la
  mediana fuera de muestra.
- psr(), dsr(), min_trl(): Probabilistic y Deflated Sharpe Ratio y longitud mínima del
  registro (Bailey y López de Prado 2012 y 2014), con asimetría y curtosis.

Entrada común: `matriz` = DataFrame con una fila por DÍA (calendario común, 0 si la variante
no operó ese día) y una columna por variante, en R netos. Todas las variantes miradas, no
solo las buenas: es la misma cuenta que `n_pruebas`.
"""
from __future__ import annotations

from itertools import combinations
from math import comb
from statistics import NormalDist

import numpy as np
import pandas as pd

_N = NormalDist()
EULER = 0.5772156649015329


def matriz_diaria(ops_por_variante: dict[str, pd.DataFrame], col: str = "r") -> pd.DataFrame:
    """Convierte {variante: DataFrame(fecha, r)} en la matriz días × variantes (0 sin operar)."""
    series = {}
    for nombre, o in ops_por_variante.items():
        f = pd.to_datetime(o["fecha"]).dt.normalize()
        series[nombre] = pd.Series(np.asarray(o[col], float), index=f).groupby(level=0).sum()
    return pd.DataFrame(series).sort_index().fillna(0.0)


# ---------------------------------------------------------------- Sharpe probabilístico
def _momentos(r):
    r = np.asarray(r, float)
    sd = r.std(ddof=1)
    if len(r) < 3 or sd == 0:
        return 0.0, 0.0, 3.0, len(r)
    z = (r - r.mean()) / r.std(ddof=0)
    return r.mean() / sd, float(np.mean(z ** 3)), float(np.mean(z ** 4)), len(r)


def psr(r, sr_ref: float = 0.0) -> float:
    """P(Sharpe verdadero > sr_ref) por observación (operación o día), con asimetría y curtosis."""
    sr, g3, g4, n = _momentos(r)
    den = 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2
    if n < 3 or den <= 0:
        return float("nan")
    return _N.cdf((sr - sr_ref) * np.sqrt(n - 1) / np.sqrt(den))


def sr_esperado_maximo(n_pruebas: int, var_sr: float) -> float:
    """Sharpe máximo esperado entre n_pruebas variantes SIN edge cuyo Sharpe varía var_sr."""
    if n_pruebas <= 1 or var_sr <= 0:
        return 0.0
    return float(np.sqrt(var_sr) * ((1 - EULER) * _N.inv_cdf(1 - 1 / n_pruebas)
                                    + EULER * _N.inv_cdf(1 - 1 / (n_pruebas * np.e))))


def dsr(r, n_pruebas: int, var_sr: float | None = None, matriz: pd.DataFrame | None = None) -> float:
    """Deflated Sharpe: PSR contra el Sharpe máximo esperado por azar entre n_pruebas.

    var_sr = varianza del Sharpe (por observación) entre las variantes probadas; si se pasa
    `matriz`, se calcula de ella. Sin ninguna de las dos, se usa la varianza del estimador
    bajo la nula (1/n), que es el caso más favorable a la estrategia.
    """
    if var_sr is None:
        if matriz is not None and matriz.shape[1] > 1:
            m = matriz.to_numpy()
            var_sr = float(np.var(m.mean(0) / m.std(0, ddof=1), ddof=1))
        else:
            var_sr = 1.0 / max(len(np.asarray(r)), 1)
    return psr(r, sr_esperado_maximo(n_pruebas, var_sr))


def min_trl(r, sr_ref: float = 0.0, confianza: float = 0.95) -> float:
    """Observaciones necesarias para afirmar Sharpe > sr_ref con esa confianza (inf si SR ≤ ref)."""
    sr, g3, g4, _ = _momentos(r)
    if sr <= sr_ref:
        return float("inf")
    return float(1 + (1 - g3 * sr + (g4 - 1) / 4 * sr ** 2) * (_N.inv_cdf(confianza) / (sr - sr_ref)) ** 2)


# ---------------------------------------------------------------- SPA / StepM
def spa(matriz: pd.DataFrame, reps: int = 2000, bloque: float | None = None,
        semilla: int = 0, alfa: float = 0.05) -> dict:
    """SPA de Hansen y StepM contra "no operar" (R = 0) con bootstrap estacionario.

    Devuelve p_spa (consistente), p_bajo/p_alto (cotas), la mejor variante y la lista de
    variantes que StepM declara superiores a no operar al nivel alfa.
    """
    from arch.bootstrap import SPA, StepM, optimal_block_length

    m = matriz.astype(float)
    if bloque is None:
        bloque = float(optimal_block_length(m.mean(axis=1)).loc[:, "stationary"].iloc[0])
        bloque = max(1.0, bloque)
    perdidas = -m                       # arch trabaja con pérdidas: menor es mejor
    base = pd.Series(0.0, index=m.index)
    s = SPA(base, perdidas, block_size=bloque, reps=reps, bootstrap="stationary", seed=semilla)
    s.compute()
    p = s.pvalues
    st = StepM(base, perdidas, size=alfa, block_size=bloque, reps=reps,
               bootstrap="stationary", seed=semilla)
    st.compute()
    medias = m.mean()
    return {"p_spa": float(p["consistent"]), "p_bajo": float(p["lower"]), "p_alto": float(p["upper"]),
            "mejor": str(medias.idxmax()), "media_mejor": float(medias.max()),
            "superiores": [str(c) for c in st.superior_models], "bloque": bloque,
            "n_variantes": m.shape[1], "n_dias": m.shape[0]}


# ---------------------------------------------------------------- PBO por CSCV
def pbo(matriz: pd.DataFrame, s: int = 16, metrica: str = "sharpe", max_combis: int = 20_000,
        semilla: int = 0) -> dict:
    """Probability of Backtest Overfitting (CSCV).

    Parte los días en `s` bloques contiguos; para cada forma de elegir s/2 bloques como
    dentro de muestra elige la mejor variante y mira su puesto en el resto. PBO = fracción
    de particiones en que esa variante queda en la mitad mala fuera de muestra.
    Orientación: < 0,2 bien; 0,2-0,5 sospechoso; > 0,5 la selección no sirve.
    """
    m = np.asarray(matriz, float)
    t, n = m.shape
    if n < 2:
        raise ValueError("PBO necesita al menos 2 variantes")
    s -= s % 2
    bloques = np.array_split(np.arange(t), s)

    def puntuar(idx):
        x = m[idx]
        if metrica == "media":
            return x.mean(0)
        sd = x.std(0, ddof=1)
        return np.divide(x.mean(0), sd, out=np.zeros(n), where=sd > 0)

    todas = combinations(range(s), s // 2)
    total = comb(s, s // 2)
    if total > max_combis:
        rng = np.random.default_rng(semilla)
        todas = (tuple(sorted(rng.choice(s, s // 2, replace=False))) for _ in range(max_combis))
    lambdas, degradacion = [], []
    for c in todas:
        dentro = np.concatenate([bloques[i] for i in c])
        fuera = np.concatenate([bloques[i] for i in range(s) if i not in c])
        p_in, p_out = puntuar(dentro), puntuar(fuera)
        mejor = int(np.argmax(p_in))
        rango = (p_out < p_out[mejor]).sum() + 0.5 * ((p_out == p_out[mejor]).sum() - 1) + 1
        w = rango / (n + 1)
        lambdas.append(np.log(w / (1 - w)))
        degradacion.append((p_in[mejor], p_out[mejor]))
    lambdas = np.array(lambdas)
    deg = np.array(degradacion)
    return {"pbo": float((lambdas <= 0).mean()), "lambda_mediana": float(np.median(lambdas)),
            "metrica_in_mejor": float(deg[:, 0].mean()), "metrica_oos_mejor": float(deg[:, 1].mean()),
            "p_oos_negativa": float((deg[:, 1] < 0).mean()), "particiones": len(lambdas)}
