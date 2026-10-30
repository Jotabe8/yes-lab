# Tendencia con operaciones largas y trailing stop: descartado en P2 (2026-10-30)

**Veredicto.** No hay EA que escribir. La regla principal (ruptura de 55 días, stop y trailing de
3 ATR, largos y cortos) no supera al placebo en 39 mercados. La única de las 18 variantes que lo
supera (100 días, trailing 4 ATR, solo largos) vive de 35 operaciones en cripto; sin cripto queda
en +0,02 R con los swaps de FTMO y en −0,17 R con costes al doble. Cae en **P2**, con n_pruebas = 27.

Preregistro: `PREREGISTRO.md`. Código: `tendencia.py`, `placebo.py`, `p2.py`. Datos: diarios de
Yahoo 1999-2026 (`datos_tendencia/`, descargados con `descargar-tendencia.yml`) y tipos de FRED.
Ajuste 2005-2022; la prueba 2023-2026 **no se ha abierto** (no hacía falta para descartar y queda
limpia para otra idea).

## Qué se probó

- Entrada: cierre por encima del máximo de N días (o por debajo del mínimo), a la apertura siguiente.
- Stop inicial 3 ATR(20); trailing chandelier (máximo desde la entrada − k ATR), vela a vela,
  huecos a la apertura. Sin objetivo. Duración media 12-41 días según el trailing.
- 39 mercados: 13 índices, 11 pares, 4 metales, 3 energías, 6 agrícolas, BTC y ETH.
- Costes: spread y **financiación nocturna con tipos reales** (largo índice paga tipo + recargo,
  forex paga o cobra el diferencial). Recargo normal (índices 2,5 %) y FTMO (índices 6,5 %, el que
  salió en el Strategy Tester del IndexBasket).

## P1: ajuste 2005-2022 (18 variantes)

| Variante | Ops/año | Días | Bruto R | Coste R | Neto R | Neto FTMO |
| --- | --- | --- | --- | --- | --- | --- |
| **55 / 3 ATR / ambos (principal)** | 200 | 23 | +0,031 | 0,053 | −0,022 | −0,062 |
| 55 / 3 ATR / largos | 114 | 25 | +0,109 | 0,068 | +0,041 | −0,009 |
| 100 / 4 ATR / largos (la mejor) | 70 | 41 | +0,279 | 0,107 | +0,172 | +0,086 |

Todas las de largos y cortos tienen neto entre −0,04 y +0,04 R. Tabla completa en `variantes_salida.txt`.

**Placebo con las mismas salidas** (entrada en día y dirección al azar, misma frecuencia, 200 réplicas):

| Variante | Bruto | Placebo medio | Placebo p95 | ¿Pasa? |
| --- | --- | --- | --- | --- |
| 55 / 3 / ambos | +0,031 | +0,015 | +0,047 | No (bruto < 3× coste y < p95) |
| 55 / 3 / largos | +0,109 | +0,086 | +0,122 | No |
| 20 / 4 / largos | +0,186 | +0,145 | +0,197 | No |
| 100 / 4 / largos | +0,279 | +0,144 | +0,215 | Sí, pero ver P2 |

Lo que gana "solo largos" es casi todo deriva alcista (índices, oro, cripto): comprar en días al
azar con el mismo trailing da casi lo mismo. En **índices** la ruptura es igual o peor que el azar
en todas las variantes; en **forex** no hay nada.

## P2: la variante 100 / 4 / largos

| Conjunto | Ops | Neto normal | Costes ×2 | Neto FTMO | FTMO ×2 |
| --- | --- | --- | --- | --- | --- |
| Cesta | 1.253 | +0,172 (t 3,4) | +0,065 | +0,086 | −0,108 |
| Sin cripto | 1.218 | +0,107 (t 2,5) | +0,001 | +0,020 | −0,174 |
| Sin cripto ni agrícolas | 1.033 | +0,075 (t 1,8) | −0,030 | −0,021 | −0,223 |
| Índices | 553 | −0,015 | −0,165 | −0,158 | −0,450 |
| Metales | 142 | +0,298 (t 1,7) | +0,173 | +0,265 | +0,108 |
| Energía | 84 | +0,204 (t 1,2) | +0,123 | +0,170 | +0,054 |
| Agrícolas | 185 | +0,287 (t 2,0) | +0,176 | +0,249 | +0,101 |
| Cripto | 35 | +2,419 (t 2,6) | +2,276 | +2,376 | +2,189 |

- Años positivos sin cripto: 61 % normal, **56 % FTMO** (< 60 %).
- Meseta (80-120 días × 3,5-4,5 ATR, sin cripto): neto normal +0,07 a +0,12, **FTMO entre −0,01 y +0,02**.
- Cripto: 35 operaciones, casi todas de BTC 2014-2021; no es una muestra, es una racha.

**Por qué cae.** Una operación tendencial dura 40 días; con un stop de 4 ATR diarios (5-8 % del
precio en un índice) la financiación de FTMO se come 0,15 R por operación en índices, más que todo
el bruto. Es la misma lección que el IndexBasket: con FTMO, lo que duerme fuera paga swap.

## ¿Qué mercados tienen tendencia?

Con estas reglas, metales, energía y agrícolas muestran algo de tendencia por encima del placebo
(+0,1 a +0,3 R), pero con 84-185 operaciones en 18 años (t 1,2-2,0) y medido sobre futuros
continuos de Yahoo sin ajustar (los saltos de vencimiento pueden fabricar rupturas). Índices y forex,
no. Ninguno da para un EA de prop por sí solo: 5-10 operaciones al año por mercado no pasan un reto.

## Límites

- Diarios de Yahoo (no Dukascopy); futuros sin ajuste de vencimiento en materias primas.
- Recargos de financiación supuestos salvo el de índices de FTMO (observado).
- Sin dividendos en índices (en un CFD largo se cobran; sumarían ~+0,04 R por operación, no cambia el veredicto).
- n_pruebas: 18 variantes + 9 de meseta = 27 (t requerido 2,9).
