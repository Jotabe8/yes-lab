"""Velas sintéticas de paseo aleatorio para probar el MOTOR de backtest (P1 del embudo).

Idea (blog MQL5 "Twelve mistakes an AI-written expert advisor makes", nº 3): si el mismo código
de backtest saca ventaja en un mercado donde no puede haberla, la ventaja la fabrica el motor
(rellenos imposibles dentro de la vela, mirar el cierre antes de entrar, stop que no se recorre
vela a vela, hueco de apertura mal tratado...).

`velas_paseo` baraja las velas reales entre días, pero cada una se queda en su minuto del día:
se conserva la forma de cada vela (hueco, máximo, mínimo, cierre relativos a la apertura), la
estacionalidad de la volatilidad (apertura de NY, noche...) y el horario, y se rompe toda
dependencia temporal. Los rendimientos se centran en 0 por minuto del día, así que el precio es
una martingala: cualquier regla de entrada y salida, simulada bien, da R bruta media ≈ 0.

Uso con el embudo:

    from metodo.sinteticos import velas_paseo
    embudo(ops, ..., paseo=lambda s: mi_backtest(velas_paseo(velas, s)).r_bruto)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def velas_paseo(velas: pd.DataFrame, semilla: int = 0, por_minuto: bool = True) -> pd.DataFrame:
    """Devuelve velas OHLC sintéticas con el mismo índice temporal que `velas`.

    velas: DataFrame con índice datetime ordenado y columnas open, high, low, close (en
    minúsculas o con mayúscula inicial). Las demás columnas (spread, volumen...) se barajan
    junto con su vela, así el coste sigue a la hora del día.
    por_minuto: True baraja solo entre velas del mismo minuto del día (recomendado para
    intradía); False baraja todas las velas (sin estacionalidad).
    """
    mapa = {c: c.lower() for c in velas.columns if c.lower() in ("open", "high", "low", "close")}
    v = velas.rename(columns=mapa)
    o, h, l, c = (v[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    if np.any(o <= 0):
        raise ValueError("precios no positivos: velas_paseo trabaja con logaritmos")
    cierre_prev = np.concatenate([[o[0]], c[:-1]])
    hueco = np.log(o / cierre_prev)            # apertura frente al cierre anterior
    lh, ll, lc = np.log(h / o), np.log(l / o), np.log(c / o)

    rng = np.random.default_rng(semilla)
    if por_minuto and isinstance(v.index, pd.DatetimeIndex):
        clave = (v.index.hour * 60 + v.index.minute).to_numpy()
    else:
        clave = np.zeros(len(v), dtype=int)
    orden = np.arange(len(v))
    for k in np.unique(clave):
        idx = np.flatnonzero(clave == k)
        orden[idx] = rng.permutation(idx)

    hueco, lh, ll, lc = hueco[orden], lh[orden], ll[orden], lc[orden]
    # Centrar el rendimiento total de cada minuto del día: sin deriva, martingala.
    total = hueco + lc
    medias = pd.Series(total).groupby(clave).transform("mean").to_numpy()
    hueco = hueco - medias                     # desplazar la vela entera conserva su forma

    # apertura i = apertura 0 + huecos hasta i + cuerpos de las velas anteriores
    log_o = np.log(o[0]) + np.cumsum(hueco) + np.concatenate([[0.0], np.cumsum(lc)[:-1]])
    sal = v.iloc[orden].copy()
    sal.index = v.index
    sal["open"] = np.exp(log_o)
    sal["high"] = np.exp(log_o + lh)
    sal["low"] = np.exp(log_o + ll)
    sal["close"] = np.exp(log_o + lc)
    return sal.rename(columns={b: a for a, b in mapa.items()})


def velas_nulo(velas: pd.DataFrame, semilla: int = 0, tipo: str = "garch", por_minuto: bool = True,
               alfa: float = 0.08, beta: float = 0.90, p_cambio: float = 0.02, ratio: float = 2.5) -> pd.DataFrame:
    """Paseo aleatorio con la volatilidad AGRUPADA por días: nulo más duro que `velas_paseo`.

    `velas_paseo` rompe toda dependencia, también la de la volatilidad, y una regla que filtra por
    volatilidad o dimensiona el stop con ATR puede "ganar" solo porque la volatilidad se agrupa en
    el mercado real y no en el paseo (Nikolopoulos, arXiv 2604.15531: falsar el proceso con nulos de
    ruido blanco, GARCH y cambio de régimen). Aquí cada día se escala por un factor de volatilidad
    que solo depende del pasado, así el precio sigue siendo una martingala (R bruta ≈ 0 para
    cualquier regla) pero hay rachas de días tranquilos y agitados.

    tipo "garch": factor de un GARCH(1,1) diario (alfa, beta). tipo "regimen": dos estados de
    volatilidad (alta = ratio × baja) con probabilidad diaria de cambio p_cambio.
    """
    base = velas_paseo(velas, semilla, por_minuto)
    mapa = {c: c.lower() for c in base.columns if c.lower() in ("open", "high", "low", "close")}
    v = base.rename(columns=mapa)
    o, h, l, c = (v[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    cierre_prev = np.concatenate([[o[0]], c[:-1]])
    hueco = np.log(o / cierre_prev)
    lh, ll, lc = np.log(h / o), np.log(l / o), np.log(c / o)

    dias = pd.DatetimeIndex(v.index).normalize() if isinstance(v.index, pd.DatetimeIndex) else np.zeros(len(v))
    cod, unicos = pd.factorize(dias)
    nd = len(unicos)
    rng = np.random.default_rng(10_000 + semilla)
    if tipo == "garch":
        w = 1.0 - alfa - beta
        s2 = np.empty(nd); s2[0] = 1.0
        for d in range(1, nd):
            eps2 = s2[d - 1] * rng.standard_normal() ** 2
            s2[d] = w + alfa * eps2 + beta * s2[d - 1]
        f = np.sqrt(s2)
    elif tipo == "regimen":
        estado = np.empty(nd, dtype=int); estado[0] = 0
        cambios = rng.random(nd) < p_cambio
        for d in range(1, nd):
            estado[d] = 1 - estado[d - 1] if cambios[d] else estado[d - 1]
        f = np.where(estado == 1, ratio, 1.0)
    else:
        raise ValueError("tipo debe ser 'garch' o 'regimen'")
    f = f / np.sqrt(np.mean(f ** 2))          # misma volatilidad media que el original
    k = f[cod]
    hueco, lh, ll, lc = hueco * k, lh * k, ll * k, lc * k
    log_o = np.log(o[0]) + np.cumsum(hueco) + np.concatenate([[0.0], np.cumsum(lc)[:-1]])
    sal = v.copy()
    sal["open"] = np.exp(log_o)
    sal["high"] = np.exp(log_o + lh)
    sal["low"] = np.exp(log_o + ll)
    sal["close"] = np.exp(log_o + lc)
    return sal.rename(columns={b: a for a, b in mapa.items()})


def sin_fuga(senal, velas: pd.DataFrame, cortes: int = 20, semilla: int = 0) -> dict:
    """Prueba de truncado contra el lookahead: la señal de cada vela no puede cambiar si se borra
    el futuro.

    senal(velas) -> Serie/array con una señal por vela (mismo índice). Se calcula con todas las
    velas y luego, en `cortes` puntos al azar, solo con las velas hasta ese punto; la señal de las
    velas anteriores al corte debe coincidir. El Deflated Sharpe no detecta una fuga (arXiv
    2608.27734: un oráculo con lookahead daba DSR 1,00), por eso esta prueba es estructural.
    """
    completa = pd.Series(np.asarray(senal(velas), float), index=velas.index)
    rng = np.random.default_rng(semilla)
    n = len(velas)
    malos = []
    for k in np.sort(rng.integers(n // 10, n - 1, cortes)):
        parcial = pd.Series(np.asarray(senal(velas.iloc[:k]), float), index=velas.index[:k])
        a, b = completa.iloc[:k].to_numpy(), parcial.to_numpy()
        dif = ~((a == b) | (np.isnan(a) & np.isnan(b)))
        if dif.any():
            malos.append((velas.index[k - 1], int(dif.sum()), velas.index[np.flatnonzero(dif)[0]]))
    detalle = ("sin fuga: la señal no cambia al borrar el futuro" if not malos else
               f"FUGA: en {len(malos)}/{cortes} cortes la señal cambia; primer caso corte {malos[0][0]}, "
               f"{malos[0][1]} velas distintas desde {malos[0][2]}")
    return {"pasa": not malos, "cortes_malos": malos, "detalle": detalle}


def prueba_motor(r_brutas: list[np.ndarray], coste_r: float | None = None) -> dict:
    """Junta las R brutas de varias réplicas sobre paseo aleatorio y mide el sesgo del motor.

    Pasa si la media no se distingue de 0 (|t| < 2). Con pocas operaciones la prueba tiene poca
    potencia: usa réplicas suficientes para tener miles de ops. Si se da el coste medio en R, el
    detalle compara el sesgo con él (un sesgo de un tercio del coste ya contamina P1).
    """
    r = np.concatenate([np.asarray(x, float) for x in r_brutas if len(x)])
    if len(r) < 30:
        return {"pasa": False, "media": np.nan, "t": np.nan, "n": len(r),
                "detalle": f"solo {len(r)} ops en el paseo aleatorio: la regla casi no opera"}
    media = float(r.mean())
    t = media / (r.std(ddof=1) / np.sqrt(len(r)))
    pasa = abs(t) < 2.0
    extra = f", {abs(media) / coste_r:.1f}× coste" if coste_r else ""
    return {"pasa": bool(pasa), "media": media, "t": float(t), "n": len(r),
            "detalle": f"R bruta en paseo aleatorio {media:+.3f} (t {t:.2f}, {len(r)} ops{extra}; debe ser ≈ 0)"}
