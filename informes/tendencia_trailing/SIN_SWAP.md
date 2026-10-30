# Lo aprendido junto: tendencia en cuenta sin swap (2026-10-30)

**Pregunta.** En todas las pruebas el bruto que aparece en diario (tendencia, cesta de índices) lo mata
la financiación nocturna. ¿Sirve la tendencia en una cuenta sin swap (swap-free)?

**Respuesta: no como tendencia; sí queda la deriva.** Sin swap, la tendencia de 100 días con trailing de 4 ATR
gana en ajuste (+0,16 R, t 3,4, sobre el placebo), pero en la prueba 2023-2026 (abierta una vez,
adenda del preregistro) da +0,12 R (t 1,3) **por debajo de comprar en días al azar con el mismo trailing
(+0,19 R)**. Con largos y cortos, −0,07 R. Lo que gana es estar comprado (deriva de índices y el oro de
2023-26), no el momento de entrada. n_pruebas acumulado 31.

| 100/4, contado (índices, forex, metales) | Ajuste 2005-22 | Prueba 2023-26 | Placebo prueba |
| --- | --- | --- | --- |
| Solo largos, sin swap | +0,160 (t 3,4) | +0,121 (t 1,3) | +0,194 |
| Solo largos, swap FTMO | −0,038 | −0,113 | |
| Largos y cortos, sin swap | +0,031 | −0,073 | −0,058 |

Por grupos en la prueba (solo largos, sin swap): metales +0,66 R, índices +0,06, forex −0,09.

**Firmas con cuentas sin swap** ([fundedtrading.com](https://fundedtrading.com/best-swap-free-prop-firms/), jul-2026, sin verificar en cada firma):
E8PRO v2 (sin swap de serie), FundedNext (+10 % de cuota), FundingPips (+10 %, solo forex y metales),
Bright Funded (complemento), FTMO y The5ers (bajo petición, coste no publicado), Funded Trading Plus (por defecto).
Avisos: algunas cobran una comisión diaria tras 3-7 días; los CFD de energía y agrícolas pagan el
contango al renovar aunque no haya swap.

**Lo útil que queda.** La única fuente de rendimiento fuera del ORB que ha aparecido varias veces es
estar comprado barato de forma continua (cesta de índices: +38.754 $ de precio en el Strategy Tester,
hundido por −66.192 $ de swap; EV/cuota positiva por la estructura de la prop incluso con media 0).
En una cuenta sin swap el IndexBasket_v100 ya escrito deja de perder por la financiación. Falta comprobar
en la firma: coste de la cuenta sin swap en índices, comisión por días y la norma de "apuestas de un solo lado".
