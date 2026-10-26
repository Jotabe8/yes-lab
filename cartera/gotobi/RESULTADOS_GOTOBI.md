# Gotobi en USDJPY: efecto real, pero no paga el coste — DESCARTADO (P1/P2)

Fecha: 2026-10-26. Método: embudo P0-P4 (`metodo/METODO.md`), preregistro en
`cartera/gotobi/PREREGISTRO.md` del PC, escrito antes de mirar datos. n_pruebas = 4.

## Idea

Los días *gotobi* (5, 10, 15, 20, 25 y último de mes; si caen en fin de semana, el hábil anterior)
las empresas japonesas liquidan facturas y los importadores compran dólares en la fijación de
Tokio de las 09:55 JST. Es un flujo obligado y documentado, justo lo que el método dice buscar.
Regla probada: comprar USDJPY a las 08:00 JST, cerrar a las 09:55, stop = 0,25 × rango diario
medio de 14 días (unos 22 pips). Datos: M1 bid/ask de Dukascopy 2018-01 a 2026-10.

## Qué sale

El efecto existe y es consistente, lo que ya es raro en este proyecto:

| Mercado | Ops gotobi | Bruto gotobi | t | Mismo horario otros días | 2018-22 | 2023-26 |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | 627 | **+0,106 R** | 3,52 | +0,022 R | +0,112 (t 2,8) | +0,098 (t 2,2) |
| EURJPY | 627 | +0,076 R | 4,83 | +0,011 R | +0,079 (t 3,8) | +0,072 (t 3,0) |
| GBPJPY | 625 | +0,073 R | 4,97 | +0,020 R | +0,081 (t 4,2) | +0,062 (t 2,8) |
| EURUSD (control, corto) | 628 | −0,043 R | −2,45 | −0,014 R | — | — |

Supera el placebo (p95 de 200 muestras de los días no gotobi: +0,059 R), se repite en los tres
cruces del yen y aguanta fuera de muestra en bruto. El control va al revés, como debía.

## Por qué se descarta igualmente

El bruto son **2,4 pips por operación** y el coste de ida y vuelta en FTMO son **1,6 pips**
(spread mediano de 0,8 pips a las 08:00 JST, que sube a 1,1 desde 2022, más 0,5 pips de comisión):

- bruto 1,5 × coste, cuando el método exige 3 × (puerta P1).
- Neto con el coste al doble: **−0,037 R/op** (puerta P2).
- Fuera de muestra neto +0,028 R con t 0,61, por debajo del t ≥ 1 exigido (puerta P3).
- La EV por cuota recortada sí daba +3.393 € frente a +1.571 € del control, pero llega después
  de tres puertas falladas y descansa sobre un margen de 0,8 pips: cualquier ensanchamiento del
  spread o un poco de slippage se lo come.

Ampliar el stop no ayuda: el margen y el coste están ambos en pips, así que la proporción
1,5 × no cambia. Y el método prohíbe añadir filtros para rescatar una idea.

**Veredicto: descartado en P1/P2.** Vale como lección: el efecto gotobi es de los pocos reales
que hemos medido, y aun así el spread del yen se lo queda entero. Confirma la lección del
proyecto (los efectos publicados valen 0,02-0,05 % por operación, lo mismo que cuesta el CFD),
esta vez con un efecto que es tres veces mayor que eso y tampoco llega.
