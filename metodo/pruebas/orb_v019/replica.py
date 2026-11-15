"""Réplica Python del ORB_US100_AGR v018/v019 sobre velas M1 de FTMO (hora del servidor, precios bid).

Reglas copiadas del .mq5 (v019 = v018 en la señal):
  - Rango 16:30-16:40 servidor (≥ 8 velas), dirección de la vela del rango, cuerpo ≥ 10 % del rango.
  - Entrada a mercado en la apertura de la vela de 16:40 (largo al ask = bid + spread).
  - Stop 15 % del ATR(14) diario (media simple del rango verdadero, barra de ayer, como iATR).
  - Trailing 3 R / 1 R (reto). Fondeada en el .set real: stop a entrada a +2 R y trailing.
  - Stop recorrido vela a vela; si la vela abre más allá del stop, sale a la apertura (hueco).
  - Cierre a las 22:30 (apertura de esa vela ≈ cierre de la de 22:29); días FOMC, a las 20:55.
  - Filtro de volatilidad: no opera si ATR%/cierre de ayer supera el p90 de los 252 días previos.
  - Festivos USA del .mq5 (2024-2027) sin operar.
  - tope_pausa (solo v019 "tope"): si el filtro bloquea pero hace ≥ N días naturales de la última
    entrada, opera igual (riesgo × 0,25: en R no cambia nada).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FESTIVOS = set(pd.to_datetime("""2024.01.01 2024.01.15 2024.02.19 2024.03.29 2024.05.27 2024.06.19 2024.07.03
2024.07.04 2024.09.02 2024.11.28 2024.11.29 2024.12.24 2024.12.25 2025.01.01 2025.01.09 2025.01.20 2025.02.17
2025.04.18 2025.05.26 2025.06.19 2025.07.03 2025.07.04 2025.09.01 2025.11.27 2025.11.28 2025.12.24 2025.12.25
2026.01.01 2026.01.19 2026.02.16 2026.04.03 2026.05.25 2026.06.19 2026.07.03 2026.09.07 2026.11.26 2026.11.27
2026.12.24 2026.12.25""".split(), format="%Y.%m.%d"))
FOMC = set(pd.to_datetime("""2024.01.31 2024.03.20 2024.05.01 2024.06.12 2024.07.31 2024.09.18 2024.11.07
2024.12.18 2025.01.29 2025.03.19 2025.05.07 2025.06.18 2025.07.30 2025.09.17 2025.10.29 2025.12.10 2026.01.28
2026.03.18 2026.04.29 2026.06.17 2026.07.29 2026.09.16 2026.10.28 2026.12.09""".split(), format="%Y.%m.%d"))

S, FLAT, FOMC_CIERRE = 16 * 60 + 30, 22 * 60 + 30, 20 * 60 + 55


def cargar(*rutas: str) -> pd.DataFrame:
    df = pd.concat([pd.read_csv(r, parse_dates=["time"]) for r in rutas])
    df = df.drop_duplicates("time", keep="last").set_index("time").sort_index()
    return df[["open", "high", "low", "close", "spread"]]


def diario(v: pd.DataFrame) -> pd.DataFrame:
    g = v.groupby(v.index.normalize()).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"),
                                           n=("open", "size"))
    # el CSV de FTMO trae D1 hasta 2021-01, H1 hasta 2021-08 y M1 después: se agregan todos
    g = g[(g.n > 60) | (g.index < "2021-09-01")]
    pc = g.c.shift(1)
    tr = np.maximum(g.h - g.l, np.maximum((g.h - pc).abs(), (g.l - pc).abs()))
    g["atr"] = tr.rolling(14).mean()
    x = (g.atr / g.c).to_numpy()
    pct = np.full(len(x), np.nan)
    for i in range(len(x)):
        if i < 120 or not np.isfinite(x[i]):
            continue
        prev = x[max(0, i - 252):i]
        prev = prev[np.isfinite(prev)]
        if len(prev) >= 120:
            pct[i] = 100.0 * (prev < x[i]).mean()
    g["pct"] = pct
    # valores de AYER para el día de hoy
    return pd.DataFrame({"atr": g.atr.shift(1), "pct": g.pct.shift(1)}, index=g.index)


def simular(v: pd.DataFrame, filtro_vol=True, festivos=True, tope_pausa=0, coste=True,
            be_fondeada: set | None = None, desde=None) -> pd.DataFrame:
    """Devuelve una fila por operación: fecha, entrada, salida (hora), lado, r, precio_entrada, ..."""
    d = diario(v)
    m_all = (v.index.hour * 60 + v.index.minute).to_numpy()
    sess = (m_all >= S) & (m_all < FLAT)
    vs = v[sess]
    ms = m_all[sess]
    filas, ultima = [], None
    dias = vs.index.normalize()
    cortes = np.flatnonzero(np.r_[True, dias[1:] != dias[:-1], True])
    for a, b in zip(cortes[:-1], cortes[1:]):
        dia = dias[a]
        if desde is not None and dia < pd.Timestamp(desde):
            continue
        if dia not in d.index or not np.isfinite(d.at[dia, "atr"]):
            continue
        if festivos and dia in FESTIVOS:
            continue
        m = ms[a:b]
        o, h, l, c = (vs[k].to_numpy()[a:b] for k in ("open", "high", "low", "close"))
        sp = vs.spread.to_numpy()[a:b] * 0.01 if coste else np.zeros(b - a)
        rng = m < S + 10
        if rng.sum() < 8 or m[0] > S + 2:
            continue
        ri = np.flatnonzero(rng)
        H, L = h[ri].max(), l[ri].min()
        cuerpo = c[ri[-1]] - o[ri[0]]
        if H - L <= 0 or abs(cuerpo) < 0.10 * (H - L):
            continue
        forzada = False
        if filtro_vol and np.isfinite(d.at[dia, "pct"]) and d.at[dia, "pct"] > 90:
            if tope_pausa and ultima is not None and (dia - ultima).days >= tope_pausa:
                forzada = True
            else:
                continue
        ei = np.flatnonzero((m >= S + 10) & (m <= S + 15))
        if not len(ei):
            continue
        k = ei[0]
        lado = 1 if cuerpo > 0 else -1
        R = 0.15 * d.at[dia, "atr"]
        fin = FOMC_CIERRE if dia in FOMC else FLAT
        sel = np.arange(k, b - a)
        sel = sel[m[sel] < fin]
        if lado == 1:
            ent = o[k] + sp[k]
            fav = h[sel] - ent
            adv = l[sel]
            oo = o[sel]
        else:
            ent = o[k]
            fav = ent - (l[sel] + sp[sel])
            adv = h[sel] + sp[sel]
            oo = o[sel] + sp[sel]
        cm = np.concatenate([[0.0], np.maximum.accumulate(fav)[:-1]])   # MFE hasta la vela anterior
        off = np.full(len(sel), -R)
        if be_fondeada is not None and dia in be_fondeada:
            off = np.where(cm >= 2 * R, 0.0, off)
        off = np.where(cm >= 3 * R, np.maximum(off, cm - R), off)
        stop = ent + lado * off
        hit = (adv <= stop) if lado == 1 else (adv >= stop)
        if hit.any():
            j = int(np.argmax(hit))
            px = stop[j] if j == 0 else (min(oo[j], stop[j]) if lado == 1 else max(oo[j], stop[j]))
            salida, tipo = vs.index[a + sel[j]], "SL"
        else:
            j = len(sel) - 1
            px = c[sel[j]] if lado == 1 else c[sel[j]] + sp[sel[j]]
            salida, tipo = vs.index[a + sel[j]] + pd.Timedelta("1min"), "EA"
        filas.append(dict(fecha=dia, entrada=vs.index[a + k], hora=salida, lado=lado,
                          r=lado * (px - ent) / R, precio_entrada=ent, stop_pts=R, salida=tipo,
                          forzada=forzada, pct=d.at[dia, "pct"]))
        ultima = dia
    return pd.DataFrame(filas)
