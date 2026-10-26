# Scalping con gestión de riesgo NNFX (2026-10-26)

**Veredicto: descartado.** De 105 combinaciones (7 mercados × 3 temporalidades × 5 entradas), ninguna gana en
neto en 2023-2026. El spread se come entre 0,02 y 0,67 R por operación y ninguna entrada tiene ventaja bruta
que lo cubra (bruto mediano +0,003 a +0,007 R, igual que la entrada aleatoria).

## Qué se probó (pre-registrado en la cabecera de `scalping.py`)

- **Datos:** velas M1 bid con spread real por minuto. EURUSD, GBPUSD, USDJPY, XAUUSD y US500 de Dukascopy;
  US100 de Dukascopy 2018-22 y FTMO 2023-26; GER40 de FTMO (escaso antes de 2022). Comisión FTMO en forex
  0,6 pips ida y vuelta.
- **Sesión:** forex y oro 10:00-19:00 servidor (Londres hasta media sesión de NY), US100/US500 16:30-22:55,
  GER40 10:00-18:25. Todo se cierra al final de la sesión: no hay swap.
- **Temporalidades:** M1, M5 y M15. ATR(14) de cada temporalidad.
- **Gestión NNFX:** SL 1,5 ATR, mitad a 1 ATR, resto a BE y trailing de 2 ATR al cierre de vela. Control 1:1
  (SL = TP = 1,5 ATR). El recorrido dentro de la vela se sigue minuto a minuto; si en un minuto tocan stop y
  objetivo, cuenta el stop. Largos entran al ask y salen al bid; cortos al revés.
- **Entradas** (señal al cierre de vela, entrada al minuto siguiente, una posición por mercado):
  - R0 aleatoria (placebo, 5 repeticiones), con gestión NNFX y con 1:1.
  - E1 retroceso a EMA20 con tendencia (EMA50 > EMA200, el mínimo toca la EMA20, cierra encima, vela alcista).
  - E2 ruptura Donchian de 20 velas a favor de la EMA200.
  - E3 RSI(2) < 10 a favor de la EMA200 (compra la caída en tendencia).
- **Criterio:** neto > 0 en ajuste (2018-22) y prueba (2023-26), t ≥ 2 en prueba, neto > 0 al doble de costes y
  mejor que R0 en la misma casilla.

## Coste del spread en R (mediana de 2023-26)

| Mercado | M1 | M5 | M15 |
|---|---|---|---|
| US100 (FTMO) | 0,066 | 0,029 | 0,018 |
| GER40 (FTMO) | 0,101 | 0,042 | 0,026 |
| US500 | 0,187 | 0,076 | 0,047 |
| USDJPY | 0,338 | 0,133 | 0,078 |
| XAUUSD | 0,353 | 0,139 | 0,083 |
| EURUSD | 0,364 | 0,148 | 0,092 |
| GBPUSD | 0,423 | 0,168 | 0,105 |

En M1, forex y oro pagan un tercio de R por operación: haría falta un acierto imposible. Solo los índices de
FTMO en M15 bajan a 0,02-0,03 R, el rango donde la Prueba 1 de la moneda aún dejaba algo por la estructura de
la prop, pero allí tampoco hay ventaja de entrada.

## Lo único positivo en ajuste, y cómo acabó en prueba

| Casilla | Neto 2018-22 (t) | Neto 2023-26 (t) |
|---|---|---|
| US100 M15 E2 ruptura Donchian | +0,078 R (3,35) | −0,006 R (−0,22) |
| GER40 M5 E1 retroceso EMA20 | +0,043 R (1,67) | −0,032 R (−2,40) |
| GER40 M15 E2 ruptura Donchian | +0,032 R (0,75) | −0,012 R (−0,55) |
| US500 M15 E2 ruptura Donchian | +0,014 R (0,60) | −0,021 R (−0,80) |

La ruptura de US100 en M15 es la misma familia que el ORB ya en vivo (momentum intradía en US100) y se apaga
después de 2022. No pasa al EV por cuota FTMO porque no supera el filtro previo.

## Ficheros

- `scalping.py` (backtest con numba sobre M1), `resumen.csv` (cada repetición), `resumen_medio.csv`.
- Reproducir: `python3 scalping.py DIR_M1 SALIDA` (DIR_M1 = `Prop Firm Challenges/data` del PC).
