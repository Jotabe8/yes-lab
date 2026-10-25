# Segunda ronda: resultados

Pruebas de `informes/ronda2-preregistro.md` con `lab/ronda2.py`. Resultados en % por
operación. Dentro de muestra hasta 2019, fuera de muestra desde 2020. Nada de esto es una
recomendación de inversión.

**Las tres ideas fallan.** En las tres hay algo de efecto antes de costes, pero el spread y el
swap de un CFD se lo comen.

## A. Rebalanceo de fin de mes en forex (D1, 2010-2025)

| Par | IS neto (t) | OOS neto (t) |
| --- | --- | --- |
| EURUSD | +0,062 (0,79) | −0,026 (−0,37) |
| GBPUSD | +0,057 (0,84) | −0,151 (−1,85) |
| AUDUSD | −0,061 (−0,73) | −0,166 (−1,68) |
| USDJPY | −0,122 (−1,14) | +0,026 (0,24) |
| **Los 4** | −0,016 (−0,37) | −0,079 (−1,74) |

Sin costes, los 4 juntos dan +0,017 % IS y −0,047 % OOS. **Descartada**: no hay efecto en
2010-2025 con esta regla.

## B. Prima nocturna de la bolsa de EE. UU. (M1)

| Serie | Sin costes IS / OOS (t) | Con costes 0,035 % IS / OOS (t) |
| --- | --- | --- |
| US500 Dukascopy 2018-2026 | +0,051 (2,09) / +0,036 (1,78) | +0,016 (0,65) / +0,001 (0,07) |
| US100 FTMO 2021-2026 | — / +0,047 (1,75) | — / +0,012 (0,45) |

El efecto existe antes de costes, como dice la literatura, pero mide unos 0,04 % por noche y
el spread más el swap de un CFD cuestan 0,035 %. Neto, 4 de 9 años negativos. **Descartada**,
como ya anticipaba el informe semanal.

## C. Oro largo en la sesión asiática (M1, 2018-2026)

| | IS (t) | OOS (t) |
| --- | --- | --- |
| Sin costes | +0,041 (2,70) | +0,074 (4,97) |
| Con costes (compra al ask de entrada) | −0,033 (−2,15) | +0,019 (1,28) |
| Costes al doble | −0,106 (−6,86) | −0,036 (−2,41) |

**Descartada.** Dos matices:

1. **Corrección de costes después de ver el resultado.** La primera versión cobraba la media del
   spread de entrada y de salida. Como los precios son bid, lo correcto es comprar al ask de
   entrada, que es el spread de entrada completo. Ese spread es alto justo antes de la pausa
   diaria (0,049 % de media frente a 0,019 % el resto del día). Con la primera versión salía
   −0,011 % IS y +0,032 % OOS (t 2,15): tampoco pasaba, porque dentro de muestra era negativa.
2. **Parte del efecto bruto es artificial.** La hora que más aporta es la reapertura tras la
   pausa (01:00 servidor). Con datos bid, el spread que se ensancha en la pausa baja el precio de
   entrada y "sube" al reabrir. Lo que queda neto, +0,02 % fuera de muestra, coincide con el oro
   subiendo con fuerza en 2023-2026.

## Lectura de conjunto

Junto con la primera ronda van unas 18 familias probadas con las reglas fijadas por adelantado.
El patrón se repite: los efectos documentados existen antes de costes, pero miden 0,02-0,05 %
por operación, y el spread y el swap de los CFD de una prop cuestan lo mismo o más. El ORB
funciona porque gana del orden de 0,1 R por operación con stops cortos, así que el coste pesa
mucho menos en proporción.
