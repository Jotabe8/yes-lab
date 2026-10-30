# Víspera de festivo en índices: descartado en P1 (2026-10-30)

**Veredicto.** El efecto existe, pero es demasiado pequeño para el coste de un CFD. Comprar la víspera de
un festivo da +0,044 R (≈ +0,06 % del precio) frente a −0,005 R de un día normal. Supera el p95 del
placebo y es positivo en 12 de 13 índices, pero el bruto es 1,8 veces el coste (se pide 3) y con costes al
doble pierde. n_pruebas = 3; la prueba 2023-2026 no se abrió.

Preregistro: `PREREGISTRO.md`. Código: `vispera.py`. Datos: diarios de Yahoo (`datos_tendencia/`),
festivos detectados con el calendario de cada índice.

| Variante (ajuste 2000-2022) | Ops/año | Bruto R | Coste R | Neto R (t) | Día normal | Placebo p95 | Años + | Neto costes ×2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A apertura → cierre | 92 | +0,044 | 0,025 | +0,019 (1,55) | −0,005 | +0,017 | 65 % | −0,006 |
| A con stop 1 ATR | 92 | +0,046 | 0,025 | +0,022 (1,82) | +0,005 | +0,027 | 61 % | −0,003 |
| B cierre → cierre (1 noche) | 92 | +0,064 | 0,047 | +0,017 (1,16) | +0,008 | +0,039 | 52 % | −0,030 |

- Por índice (A): GER40, SPA35 y UK100 +0,09 R; EE. UU. +0,04-0,06 R; JP225 −0,02 R.
- Las 92 operaciones al año se concentran en pocas fechas (Navidad, Año Nuevo, Semana Santa), en las que
  todos los índices se mueven juntos, así que el t real es aún menor.
- Es la lección de siempre: los efectos publicados ganan 0,02-0,06 % por operación, lo que cuesta el CFD.
