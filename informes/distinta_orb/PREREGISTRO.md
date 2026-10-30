# Preregistro · Buscar un sistema distinto al ORB (2026-10-30)

Escrito antes de mirar los datos. Dos ideas que no están en la lista de descartadas
(la búsqueda de 25.000 reglas usó horas fijas y el movimiento reciente del propio mercado;
ninguna de estas dos).

## A. Periodicidad intradía (Heston, Korajczyk y Sadka 2010; Bogousslavsky 2016)
- Regla: en cada media hora de la sesión de contado de cada índice, ir en la dirección de la
  media de la MISMA media hora en los últimos 20 días hábiles (A1) o en los mismos días de la
  semana de las últimas 8 semanas (A2). Mantener 30 min. Sin optimizar.
- Mercados: US500, US100, US30, US2000, GER40, UK100, FRA40, EU50, JP225 y XAUUSD (M1 del PC, hora servidor).
- Periodo: ajuste 2018-2022; 2023-2026 cerrado hasta P3.
- Métrica: bruto medio por operación en pb y en múltiplos del spread; placebo: la señal de
  otra media hora elegida al azar (200 réplicas).
- Umbral P1: bruto ≥ 3 × coste, por encima del p95 del placebo y positivo en ≥ 6 de 10 mercados.

## B. Deriva tras el inventario de crudo de la EIA (miércoles 10:30 NY = 17:30 servidor)
- Regla: dirección del movimiento 10:30→10:35 NY; entrar a las 10:35 y salir a las 11:30 (B1)
  o a las 14:30 NY, cierre del parqué (B2). Sin stop en P1.
- Mercado: USOIL (M1 FTMO, desde 2021). Ajuste 2021-2022; 2023-2026 cerrado.
- Placebo: la misma regla a la misma hora los lunes, martes, jueves y viernes (sin dato) y
  dirección aleatoria.
- Umbral P1: bruto ≥ 3 × coste y miércoles por encima del p95 del placebo de otros días.

n_pruebas previstas: A = 2 reglas × 10 mercados = 20; B = 2. Total 22 (t requerido ≈ 2,8).
