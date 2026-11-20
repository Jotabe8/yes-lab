"""v16 — datos comunes: 5 mercados elegidos al azar (semilla 20261120) en M5, precio medio, UTC.

Universo: las 15 cachés Dukascopy M1 bid/ask completas 2018-2026 del PC de Jorge
(AUS200, ESP35, EURUSD, EU50, FRA40, GBPUSD, UK100, HK50, JP225, NL25, US30, US500, USDJPY,
US2000, XAUUSD; GER40 fuera porque su caché acaba en 2024-03).
numpy.random.default_rng(20261120).choice(universo_ordenado, 5, replace=False) ->
EURUSD, GBRIDXGBP (UK100), JPNIDXJPY (JP225), USA500IDXUSD (US500), XAUUSD.

Coste de ida y vuelta (fracción del precio): horquilla real FTMO en la 1.ª hora de apertura
(metodo/v3/spread_aperturas_ftmo.csv) + 0,2 pb de deslizamiento, o media horquilla Dukascopy de la vela de
entrada + 0,2 pb si es mayor (Dukascopy exagera la horquilla 1,6-2× frente a FTMO; fuera de la
hora buena la de FTMO también se abre). US500 no está en la tabla: 0,6 pb (como US100/GER40). EURUSD: 0,1 pip
de horquilla + comisión FTMO 5 $/lote i/v ≈ 0,55 pb.
"""
from __future__ import annotations

import glob
import os

import numpy as np

UNIVERSO = sorted(['AUSIDXAUD', 'ESPIDXEUR', 'EURUSD', 'EUSIDXEUR', 'FRAIDXEUR', 'GBPUSD',
                   'GBRIDXGBP', 'HKGIDXHKD', 'JPNIDXJPY', 'NLDIDXEUR', 'USA30IDXUSD',
                   'USA500IDXUSD', 'USDJPY', 'USSC2000IDXUSD', 'XAUUSD'])
SEMILLA = 20261120
MERCADOS = sorted(np.random.default_rng(SEMILLA).choice(UNIVERSO, 5, replace=False).tolist())
NOMBRE = {'EURUSD': 'EURUSD', 'GBRIDXGBP': 'UK100', 'JPNIDXJPY': 'JP225',
          'USA500IDXUSD': 'US500', 'XAUUSD': 'XAUUSD'}
# coste i/v en fracción del precio (FTMO + 0,2 pb deslizamiento)
COSTE = {'EURUSD': 0.55e-4 + 0.2e-4, 'GBRIDXGBP': 0.79e-4 + 0.2e-4, 'JPNIDXJPY': 1.57e-4 + 0.2e-4,
         'USA500IDXUSD': 0.60e-4 + 0.2e-4, 'XAUUSD': 0.99e-4 + 0.2e-4}
DIR = os.environ.get('V16_DATOS', os.path.join(os.path.dirname(__file__), '..', '..', '..', 'datos_v16'))
FIN_EXPLORACION = 20221231


def cargar(m: str):
    """dias (int yyyymmdd), x (n,288,6) con o,h,l,c medio, horquilla media, nº velas M1."""
    fs = sorted(glob.glob(os.path.join(DIR, f'm5_{m}_*.npz')))
    d, x = [], []
    for f in fs:
        z = np.load(f)
        d.append(z['dias']); x.append(z['x'])
    d = np.concatenate(d); x = np.concatenate(x).astype(np.float64)
    o = np.argsort(d)
    d, x = d[o], x[o]
    # fuera fines de semana (velas sueltas del domingo) y días casi vacíos
    wd = np.array([np.datetime64(f'{s // 10000:04d}-{s // 100 % 100:02d}-{s % 100:02d}').astype('datetime64[D]').item().weekday() for s in d])
    ok = (wd < 5) & (np.isfinite(x[:, :, 3]).sum(1) >= 60)
    return d[ok], x[ok]


def todos():
    return {m: cargar(m) for m in MERCADOS}
