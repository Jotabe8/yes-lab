# Machine learning intradía (regla rota: búsqueda masiva) — DESCARTADO

LightGBM (2 modelos: largo y corto) con 20 características (movimiento desde la apertura, rango y posición, día previo, 5 y 20 días, hueco, régimen de volatilidad, día de la semana, movimiento de los otros 3 índices). Entrada al inicio de cada barra de 30 min (10:00 a 15:00), stop 0,15 ATR, salida al cierre. US100/US500/US30/US2000, 2012-2026, coste FTMO aprox. Walk-forward anual: entrena con los años anteriores y opera 2016-2026 sin ver el año. Cada día y mercado, la mejor predicción si > umbral.

| Umbral | Ops | R/op | t |
|---|---|---|---|
| 0 | 8.122 | −0,076 | −3,3 |
| 0,1 | 6.009 | −0,071 | −2,7 |
| 0,2 | 4.211 | −0,066 | −2,0 |

Solo 2018, 2021 y 2022 positivos; US100 ≈ 0, US2000 −0,2 R. El modelo no generaliza: confirma el atlas (no hay señal combinable en estas variables).
