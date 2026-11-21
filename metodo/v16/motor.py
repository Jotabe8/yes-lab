"""v16 — motor común: rasgos medidos ANTES de la entrada y operación intradía con stop vela a vela.

Entrada en la apertura (precio medio) de la vela M5 `b`; salida al cierre de la vela b+H-1 o en el
stop. El stop se revisa vela a vela: si la vela abre ya más allá del stop, se sale en la apertura
(hueco). R = dirección·(salida−entrada)/distancia_stop. Distancia = k·ATR14 diario (media del rango
alto-bajo de los 14 días anteriores, sin el día de hoy).
"""
from __future__ import annotations

import numpy as np

from metodo.v16.datos import COSTE

RASGOS = ['r1h', 'rdia', 'rayer', 'volsorpresa', 'posrango', 'cruzado1h']


class Mercado:
    def __init__(self, m, dias, x):
        self.m, self.dias = m, dias
        self.O, self.H, self.L, self.C, self.S = (x[:, :, i] for i in range(5))
        n = len(dias)
        hi = np.nanmax(self.H, 1); lo = np.nanmin(self.L, 1)
        self.hi, self.lo = hi, lo
        rng = hi - lo
        self.atr = np.full(n, np.nan)
        for i in range(14, n):
            self.atr[i] = np.nanmean(rng[i - 14:i])
        first = np.array([row[np.isfinite(row)][0] for row in self.O])
        last = np.array([row[np.isfinite(row)][-1] for row in self.C])
        self.apertura_dia = first
        self.rdia_total = last / first - 1
        self.rayer = np.r_[np.nan, self.rdia_total[:-1]]
        self.hi_ayer = np.r_[np.nan, hi[:-1]]; self.lo_ayer = np.r_[np.nan, lo[:-1]]
        lr = np.abs(np.diff(np.log(self.C), axis=1, prepend=np.nan))
        self.absr = lr
        self.exp = dias <= 20221231
        self.coste = COSTE[m]
        self.cruz = None  # lo rellena `cruzar`

    def ffill_open(self, b):
        """Apertura de la vela b; si falta, nan."""
        return self.O[:, b]

    def rasgo(self, nombre, b):
        O = self.O
        if nombre == 'r1h':
            return O[:, b] / O[:, b - 12] - 1 if b >= 12 else np.full(len(O), np.nan)
        if nombre == 'rdia':
            return O[:, b] / self.apertura_dia - 1
        if nombre == 'rayer':
            return self.rayer
        if nombre == 'volsorpresa':
            if b < 12:
                return np.full(len(O), np.nan)
            v = np.nansum(self.absr[:, b - 12:b], 1)
            v[np.isfinite(self.absr[:, b - 12:b]).sum(1) < 9] = np.nan
            base = np.full(len(v), np.nan)
            for i in range(20, len(v)):
                w = v[i - 20:i]
                if np.isfinite(w).sum() >= 10:
                    base[i] = np.nanmean(w)
            return v / base
        if nombre == 'posrango':
            return (O[:, b] - self.lo_ayer) / (self.hi_ayer - self.lo_ayer)
        if nombre == 'cruzado1h':
            return self.cruz[b] if self.cruz is not None else np.full(len(O), np.nan)
        raise KeyError(nombre)

    def adelante(self, b, H):
        """Rendimiento medio de la apertura de b al cierre de b+H-1 (fracción)."""
        if b + H > 288:
            return np.full(len(self.O), np.nan)
        return self.C[:, b + H - 1] / self.O[:, b] - 1

    def operar(self, b, H, k, direccion):
        """direccion: array (+1/−1/0) por día. Devuelve R bruta y coste en R (nan si no opera)."""
        n = len(self.O)
        e = self.O[:, b]
        s = k * self.atr
        d = np.asarray(direccion, float)
        R = np.full(n, np.nan); vivo = np.isfinite(e) & np.isfinite(s) & (s > 0) & (d != 0)
        salida = np.full(n, np.nan)
        abierto = vivo.copy()
        stop = e - d * s
        ultimo = np.full(n, np.nan)
        for j in range(b, min(b + H, 288)):
            o, h, l, c = self.O[:, j], self.H[:, j], self.L[:, j], self.C[:, j]
            ok = abierto & np.isfinite(o)
            # hueco más allá del stop en la apertura
            gap = ok & (d * (o - stop) <= 0)
            salida[gap] = o[gap]; abierto &= ~gap
            ok &= ~gap
            toca = ok & (((d > 0) & (l <= stop)) | ((d < 0) & (h >= stop)))
            salida[toca] = stop[toca]; abierto &= ~toca
            ultimo = np.where(ok & np.isfinite(c), c, ultimo)
        resto = abierto & np.isfinite(ultimo)
        salida[resto] = ultimo[resto]
        R[vivo] = (d * (salida - e) / s)[vivo]
        spr = self.S[:, b] / e
        coste_frac = np.maximum(self.coste, np.nan_to_num(spr, nan=0) / 2 + 0.2e-4)
        cR = coste_frac * e / s
        cR[~np.isfinite(R)] = np.nan
        return R, cR


def cruzar(mercados: dict, barras=None):
    """cruzado1h: media de r1h z-normalizada (σ de exploración) de los OTROS 4 mercados en la
    misma vela UTC; nan si hay menos de 2 con dato."""
    barras = range(12, 288) if barras is None else barras
    import pandas as pd
    for M in mercados.values():
        M.cruz = {}
    for b in barras:
        z = {}
        for m, M in mercados.items():
            r = M.rasgo('r1h', b)
            sd = np.nanstd(r[M.exp])
            z[m] = pd.Series(r / sd if sd > 0 else r * np.nan, index=M.dias)
        df = pd.DataFrame(z)
        for m, M in mercados.items():
            otros = df.drop(columns=m)
            v = otros.mean(axis=1).where(otros.notna().sum(axis=1) >= 2)
            M.cruz[b] = v.reindex(M.dias).to_numpy()
    return mercados


def horas_liquidas(M: Mercado, minimo=0.9):
    """Velas M5 con dato en ≥ 90 % de los días de exploración y horquilla Duka ≤ 2× la mediana."""
    cob = np.isfinite(M.O[M.exp]).mean(0)
    spr = np.nanmedian(M.S[M.exp] / M.O[M.exp], 0)
    med = np.nanmedian(spr[cob >= minimo])
    return np.where((cob >= minimo) & (spr <= 2 * med))[0]
