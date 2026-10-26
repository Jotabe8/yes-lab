# Prima nocturna tras un día de estrés — DESCARTADA (corrección del 2026-10-26)

**Este informe sustituye al publicado una hora antes, que daba la idea por buena. Aquel resultado
venía de un fallo del backtest y no vale. No usar `NocheEstres_v100.mq5`.**

## Qué falló

El primer backtest calculaba cada operación como `max((precio_de_salida − entrada) / stop, −1)`.
Eso aplica el stop solo mirando el precio de la mañana siguiente:

- si el precio tocaba el stop de madrugada y luego se recuperaba, contaba la recuperación, cuando
  en la realidad el stop ya habría cerrado la operación con −1 R;
- y si abría con un hueco por debajo del stop (fines de semana, marzo de 2020, aranceles de abril
  de 2025), lo dejaba en −1 R, cuando el hueco se llena al precio de apertura (hasta −6,8 R).

Es decir, un stop que corta las pérdidas grandes pero nunca salta en las caídas que se recuperan.
Eso fabricó todo el edge.

## Con el recorrido completo de la noche

Se ha repetido cada operación vela a vela (M1) desde el cierre hasta la salida: el stop salta en
la primera vela que lo toca y se llena al peor de stop o apertura.

| Mercado | Ops | Bruto antes (con fallo) | Bruto real | Sin viernes |
| --- | --- | --- | --- | --- |
| US500 | 95 | +0,194 | −0,139 | −0,060 |
| US30 | 86 | +0,237 | −0,124 | +0,006 |
| US2000 | 155 | +0,202 | −0,100 | −0,057 |
| FRA40 | 127 | +0,166 | −0,050 | +0,053 |
| EU50 | 138 | +0,211 | −0,014 | +0,068 |
| UK100 | 76 | +0,121 | −0,090 | +0,172 |
| GER40 | 60 | +0,089 | −0,143 | −0,025 |
| **Todos** | **737** | **+0,183** | **−0,086 (t −1,9)** | — |

Neto real −0,112 R/op, −0,115 en 2018-22 y −0,103 en 2023-26. Salidas: 557 por hora, 133 por
stop dentro de la noche y 47 por hueco. Sin stop (solo salida por hora) el bruto es +0,005 R,
por debajo de las noches normales (+0,059 R): quedarse con las noches de estrés no añade nada.

**Veredicto: descartada en P1** (bruto negativo). No tiene sentido simular el año en FTMO: con
−0,11 R por operación el resultado sería perder cuotas.

## Lección para el método

Toda salida por stop se comprueba recorriendo las velas entre entrada y salida, y los huecos se
llenan a la apertura. Recortar el resultado final a −1 R es mirar el futuro.
