# Variantes del mecanismo ORB (2012-2026) — ninguna es un sistema nuevo

Preregistro: PREREGISTRO_ORB_VARIANTES.md. Réplica Python con M1 bid/ask Dukascopy (spread incluido en r).

## Primera pasada (neto R por operación)
| Variante | 2018-22 | 2023-26 | Corr con v018 real |
|---|---|---|---|
| US100 rango 5 min | +0,19 | +0,15 | 0,63 |
| US100 rango 10 min (réplica) | +0,22 | +0,13 | 0,78 |
| US100 rango 15 min | +0,13 | +0,17 | 0,64 |
| US100 rango 30 min | +0,18 | +0,02 | 0,48 |
| **US100 rango 60 min** | +0,09 | +0,14 | **0,27** |
| US100 entrada en contra tras stop | +0,01 | +0,03 | −0,07 |
| US500 rangos 5-60 min | +0,05 a +0,12 | −0,07 a +0,08 | 0,17-0,44 |
| US30 rangos 5-60 min | +0,02 a +0,05 | −0,16 a −0,02 | 0,05-0,17 |

Las de rango corto (5-15 min) funcionan pero son el mismo ORB (corr 0,6-0,8). US30 no funciona; la entrada en contra tampoco.

## Candidata: ORB de 60 min en US100 (rango 9:30-10:30, entrada 10:30)
- 2018-26: +0,112 R/op, t 2,26, corr 0,27 con el ORB real. 2012-17 bruto +0,16 R (neto ≈ 0 por coste de entonces).
- Placebo (mismo momento y salidas, lado contrario): el exceso por elegir el lado es +0,02 R (t 0,3) en 2018-22 y +0,13 R (t 2,2) en 2023-26. Casi todo el rendimiento de 2018-22 viene de la forma del pago (stop corto en días de tendencia), no de acertar el lado.
- EV 2-Step 100K (embudo.py, cuota 540): ORB solo al 2 % 5.600 €; ORB 1 % + ORB60 1 % 6.300-6.600 €; con ORB60 de lado al azar 5.200 € de media (rango 4.000-7.000); con costes ×2 5.000-5.500 €.

Veredicto: el ORB60 no supera de forma fiable a su placebo ni a costes ×2. Descartado como sistema nuevo. Conclusión del giro: el mecanismo del ORB está ya explotado por el EA v018; sus variantes o son el mismo sistema o no tienen edge propio.
