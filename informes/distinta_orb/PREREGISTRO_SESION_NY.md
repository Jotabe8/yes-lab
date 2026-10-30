# Preregistro · Dirección de la sesión de NY con información de otros mercados (2026-10-30)

Escrito antes de mirar los datos. Aplica lo aprendido del mapa de coste: ventana más barata
(apertura de contado de NY → cierre, coste ≈ 0,7-1,6 % del movimiento), una operación al día,
recorrido de horas, sin swap. No es una ruptura: la dirección se decide a las 9:30 NY con datos
de OTROS mercados, antes de ver el precio de la sesión.

- Regla: a las 16:30 servidor (9:30 NY) se predice el signo del rendimiento apertura→22:30 servidor con
  una regresión ridge sobre 7 variables, reentrenada cada 20 días solo con el pasado (mínimo 250 días):
  noche del propio índice (22:30 anterior → 16:30), GER40 desde su apertura (10:00 → 16:30), oro, USDJPY
  y EURUSD en la noche, US2000 menos US100 en la noche, y rendimiento apertura→cierre de ayer del índice.
  Se opera en la dirección de la predicción; salida 22:59 servidor. Sin stop en P1.
- Mercados: US100, US500, US30, US2000 (M1 del PC).
- Periodo: ajuste 2019-2022; 2023-2026 cerrado hasta P3.
- Métrica: bruto medio por operación (pb) contra el spread; placebo: el mismo modelo con las fechas
  de las variables barajadas (100 réplicas).
- Umbral P1: bruto ≥ 3 × coste, por encima del p95 del placebo en ≥ 3 de 4 mercados.
n_pruebas: 1 modelo × 4 mercados = 4 (acumulado del hilo 45).
