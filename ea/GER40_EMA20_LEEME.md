# GER40_EMA20_v100: cómo probarlo en el Strategy Tester

Este EA es la réplica de `informes/scalping_nnfx/coste_bajo.py`, en concreto la entrada E1 con la gestión G2 y sin filtro de coste. Todavía no está compilado ni probado en MT5.

## Reglas

- **Gráfico y vela de señal:** GER40.cash en M30, con hora de servidor FTMO.
- **Ventana de señal:** la vela de señal tiene que cerrar entre las 10:30 y las 11:30, es decir, las velas que abren a las 10:00, 10:30 y 11:00.
- **Largo:** la EMA50 está por encima de la EMA200, el mínimo de la vela toca la EMA20, la vela cierra por encima de la EMA20 y es alcista. El corto es el caso simétrico.
- **Entrada:** a mercado al abrir la vela siguiente.
- **Stop:** 1,5 ATR(14) de M30, con el riesgo en % del balance.
- **Gestión:** al ganar +1 ATR, el stop pasa a break even. A partir de ahí, al cierre de cada vela M30, se aplica un trailing de 2 ATR. No hay objetivo.
- **Cierre forzoso:** a las 18:25. Como máximo 2 operaciones al día y una abierta a la vez.

## Configuración del Strategy Tester

- **Símbolo:** GER40.cash, en M30.
- **Modelado:** "Cada tick basado en ticks reales".
- **Fechas:** 2022-01-01 a 2026-10-23, que es el tramo con datos FTMO en Python.
- **Depósito y riesgo:** 100.000 y `InpRiskPct` = 1,0. El resto de parámetros, por defecto.

## Qué debería salir (Python, datos FTMO 2022-2026)

| Año | Ops | R medio | R total |
|---|---|---|---|
| 2022 | 129 | +0,26 | +33,8 |
| 2023 | 111 | +0,14 | +15,1 |
| 2024 | 113 | +0,06 | +6,7 |
| 2025 | 107 | +0,42 | +45,2 |
| 2026 | 101 | +0,15 | +15,4 |
| **Total** | **561** | **+0,21** | **+116 R** |

En total acierta el 23 % de las operaciones y la peor racha de caída es de unos 15 R. Al 1 % de riesgo, eso equivale a ganar alrededor de un +116 % sin interés compuesto, con una caída máxima de alrededor del 15 %.

## Diferencias esperables

- Python mira el máximo y el mínimo de cada minuto, y si en un mismo minuto se tocan el BE y el stop, cuenta el stop. MT5 va tick a tick, así que el resultado debería ser igual o algo mejor.
- Si reinicias el EA con una posición abierta, pierde el ATR de entrada y el BE no se mueve. En el probador no ocurre.
- Si el número de operaciones se aleja más de un 10 % de la tabla, o el R medio cae por debajo de +0,10, avísame con el informe del probador y lo comparo operación a operación.
