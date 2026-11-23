"""Núcleos rápidos (Numba) para simular el ORB y sus placebos sobre las matrices M1 de `metodo/v9/datos/*_m1.npz`.

Formato de entrada (lo genera `metodo/v9/extraer.py`): x[día, minuto, campo] con minuto 0 = 07:00 NY y 600 minutos
(hasta 16:59); campos open, high, low, close (precio medio) y spr (horquilla al cierre del minuto).

Lógica = réplica del ORB US100 (`orb_acciones/orb_us100.py`) en precio medio: rango 9:30-9:40, lado de la vela del rango
si el cuerpo es >= 10 % del rango, entrada a las 9:40, stop 0,15 × ATR14 (sesión 9:30-16:00, del día anterior), salida
a las 15:55. Devuelve la R bruta; el coste se resta fuera (spr en la entrada / distancia del stop).

`orb_r(x, atr, lados)` acepta un vector de lados forzados (+1/−1, 0 = usar la vela) para correr placebos de dirección
aleatoria con las mismas salidas. Sin Numba instalado funciona igual, solo que lento (mismo código en Python).

Uso:
    from metodo.rapido import cargar, atr_sesion, orb_r, placebo_direccion
    fechas, x = cargar("metodo/v9/datos/US100_2019_m1.npz")
    r = orb_r(x, atr_sesion(x), np.zeros(len(x), np.int8))
"""
from __future__ import annotations

import numpy as np

try:
    from numba import njit, prange
except ImportError:  # sin Numba: mismo código, en Python puro
    def njit(*a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f
    prange = range

K_INI, K_RANGO_FIN, K_SALIDA, K_SES_FIN = 150, 160, 535, 540  # 9:30, 9:40, 15:55, 16:00 desde las 07:00


def cargar(ruta):
    z = np.load(ruta)
    return z["fechas"], z["x"].astype(np.float64)


def atr_sesion(x, n=14):
    """ATR de n días de la sesión 9:30-16:00, desplazado un día (solo información anterior)."""
    s = x[:, K_INI:K_SES_FIN, :]
    ok = np.isfinite(s[:, :, 1]).any(1)  # días con sesión (los festivos vienen vacíos y se saltan)
    v = s[ok]
    h, l = np.nanmax(v[:, :, 1], 1), np.nanmin(v[:, :, 2], 1)
    c = np.array([row[np.isfinite(row)][-1] for row in v[:, :, 3]])
    pc = np.r_[np.nan, c[:-1]]
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    atr_v = np.full(len(v), np.nan)
    if len(v) > n:
        atr_v[n:] = np.convolve(tr, np.ones(n) / n, "valid")[:-1]  # media de los n días con sesión anteriores
    out = np.full(len(x), np.nan)
    out[ok] = atr_v
    return out


@njit(cache=True)
def _un_dia(d, a, lado_forzado):
    """R bruta de un día (nan si no opera). d: matriz 600×5 del día."""
    if not np.isfinite(a) or a <= 0:
        return np.nan
    o = d[K_INI, 0]
    c = d[K_RANGO_FIN - 1, 3]
    h, l = -1e300, 1e300
    for k in range(K_INI, K_RANGO_FIN):
        if not np.isfinite(d[k, 1]):
            return np.nan
        h = max(h, d[k, 1]); l = min(l, d[k, 2])
    if h - l <= 0 or not np.isfinite(o) or not np.isfinite(c):
        return np.nan
    if abs(c - o) < 0.10 * (h - l):
        return np.nan
    lado = 1.0 if c > o else -1.0
    if lado_forzado != 0:
        lado = float(lado_forzado)
    ent = d[K_RANGO_FIN, 0]
    if not np.isfinite(ent):
        return np.nan
    dist = 0.15 * a
    stop = ent - lado * dist
    for k in range(K_RANGO_FIN, K_SALIDA):
        if not np.isfinite(d[k, 1]):
            continue
        if lado > 0 and d[k, 2] <= stop:
            px = stop if k == K_RANGO_FIN else min(stop, d[k, 0])
            return (px - ent) / dist
        if lado < 0 and d[k, 1] >= stop:
            px = stop if k == K_RANGO_FIN else max(stop, d[k, 0])
            return (ent - px) / dist
    px = d[K_SALIDA, 0]
    if not np.isfinite(px):
        return np.nan
    return lado * (px - ent) / dist


@njit(cache=True, parallel=True)
def orb_r(x, atr, lados):
    """R bruta por día (nan = no opera). lados[i] = 0 usa la vela del rango; ±1 fuerza la dirección."""
    out = np.empty(x.shape[0])
    for i in prange(x.shape[0]):
        out[i] = _un_dia(x[i], atr[i], lados[i])
    return out


def orb_r_python(x, atr, lados):
    """La misma simulación sin compilar (referencia para tests y para medir la mejora)."""
    f = getattr(_un_dia, "py_func", _un_dia)
    return np.array([f(x[i], atr[i], lados[i]) for i in range(len(x))])


def placebo_direccion(x, atr, replicas=200, semilla=0, motor=None):
    """Media de R bruta de `replicas` series con dirección aleatoria y las mismas salidas (mismos días operados)."""
    motor = motor or orb_r
    rng = np.random.default_rng(semilla)
    medias = np.empty(replicas)
    for j in range(replicas):
        lados = rng.choice(np.array([-1, 1], np.int8), len(x))
        medias[j] = np.nanmean(motor(x, atr, lados))
    return medias
