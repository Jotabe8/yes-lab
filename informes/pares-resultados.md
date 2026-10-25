# Valor relativo (pares): resultados

Prueba de `informes/pares-preregistro.md` con `lab/pares.py`, Dukascopy D1 2010-2025.
Dentro de muestra hasta 2019, fuera de muestra 2020-2025. Resultados en % del capital por
operación con el par escalado a una volatilidad del 1 % diario. Nada de esto es una
recomendación de inversión.

## Regla corregida (β de hoy sobre la ventana del z), costes normales

| Par | n IS | media IS | t IS | n OOS | media OOS | t OOS |
| --- | --- | --- | --- | --- | --- | --- |
| US500/US100 | 42 | −1,68 | −2,40 | 53 | −1,67 | −2,94 |
| US500/US30 | 40 | −1,89 | −2,76 | 38 | −1,74 | −2,27 |
| US500/US2000 | 0 | | | 49 | −1,13 | −1,25 |
| GER40/EU50 | 39 | −1,63 | −2,81 | 43 | −0,74 | −1,40 |
| FRA40/EU50 | 47 | −1,89 | −3,07 | 39 | −1,95 | −2,77 |
| GER40/FRA40 | 38 | +0,18 | 0,26 | 44 | −1,13 | −1,75 |
| UK100/EU50 | 41 | −0,55 | −0,92 | 40 | −0,09 | −0,16 |
| Oro/plata | 58 | −1,64 | −2,31 | 50 | −1,99 | −2,32 |
| EURUSD/GBPUSD | 72 | −0,51 | −1,18 | 45 | +0,60 | 1,28 |
| AUDUSD/NZDUSD | 67 | −0,97 | −2,00 | 39 | −2,14 | −2,64 |
| Brent/WTI | 58 | +0,21 | 0,42 | 47 | +0,78 | 2,39 |
| **Todos** | 502 | −0,99 | −5,27 | 487 | −1,01 | −4,89 |

Pares positivos fuera de muestra: 2 de 11. **No pasa.**

| Costes | media IS (t) | media OOS (t) | pares OOS > 0 |
| --- | --- | --- | --- |
| Sin costes | +0,06 (0,32) | −0,08 (−0,40) | 4/11 |
| Normales | −0,99 (−5,27) | −1,01 (−4,89) | 2/11 |
| Al doble | −2,04 (−10,1) | −1,94 (−8,97) | 0/11 |

La versión original del preregistro (`--beta-diario`) da lo mismo: −1,51 % IS y −0,98 % OOS
(t −3,3), y sin costes −0,20 % / +0,27 % (t 0,9).

## Sensibilidad (sin costes, solo informativa)

De las 9 combinaciones de umbral (1,5 / 2 / 2,5) y ventana (20 / 60 / 120), ninguna es positiva
fuera de muestra con la regla corregida (de −0,04 % a −0,39 %). Con costes, todas pierden con
t entre −4 y −8.

## Lectura

1. **No hay edge ni antes de costes.** Entre mercados tan parecidos el desajuste diario no
   revierte de forma aprovechable en 2010-2025.
2. **Los costes de CFD lo hunden.** Para que un par muy correlacionado mueva el 1 % diario hacen
   falta 2-5 veces el capital en cada pata, y la financiación de las dos patas (3 % anual cada
   una) se come cerca del 1 % por operación de 2-3 semanas.
3. **Brent/WTI** es el único par positivo en los dos periodos (+1,6 % por operación sin costes
   fuera de muestra, t 5). No cuenta como hallazgo: no se eligió de antemano y las series
   continuas de Dukascopy cambian de contrato en fechas distintas para Brent y WTI, lo que crea
   saltos falsos en el diferencial que luego "revierten". Para comprobarlo harían falta series
   ajustadas por vencimiento y el spread real de FTMO en los dos petróleos.

**Veredicto: descartado.** No se reajusta.
