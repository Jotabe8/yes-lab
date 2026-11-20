# v17 — Mejorar el método de búsqueda con lo que dice internet (20-11-2026)

Pedido de Jorge: investigar en webs/foros/papers cómo mejorar la búsqueda de estrategias y PONERLO A PRUEBA,
en rondas. No se repiten las mejoras del PR #52 (t por semana, libro de pruebas, plantadas, nulos GARCH) ni lo
que el embudo ya tiene (DSR, PBO/CSCV, SPA/StepM, PSR, MinTRL, placebo, paseo aleatorio).

## Banco de pruebas: la cohorte (metodo/v17/cohorte.py)
4.284 reglas diarias reales (9 familias de rejilla × 2 lados × 37 mercados: índices, divisas, energía, metales,
agrícolas, bonos), datos diarios ya en el repo. Ajuste 2001-14 (mitades A 2001-07, B 2008-14), fuera 2015-26.
Coste 0,01 ATR por lado. Objetivo principal `tx` = R sin deriva (pos × (ret − media del tramo)), que es lo que
mide el placebo; secundario `t` = con exposición. Control positivo: IBS largo en índices US (la reversión DZ).

Criterio de "mejora del método": un rasgo de ajuste mejora si su Spearman con el t fuera supera al del t de
ajuste con IC 95 % (bootstrap por mercados, 500 reps) que excluye 0 **en los dos objetivos**, y el top 5 % que
elige no tiene peor t fuera que el top 5 % por t.

## Ronda 1 (exploratoria: rasgos fijados en analizar.py antes de mirar; criterio arriba)
Rasgos: meseta (media de la regla y sus vecinos de rejilla), cruzado (misma regla en los demás mercados de
la clase), estabilidad (mín. de las dos mitades), WFC (Tinsley: corr. A-B de la rejilla), EB jerárquico
(Chen-Dim), volatilidad y DD (Wiecki).

## Ronda 1-bis (confirmación preregistrada ANTES de correr, 20-11 ~23:55 UTC)
El ganador de la ronda 1 (meseta y meseta+cruzado) se confirma en OTRO corte: ajuste 2001-10, fuera 2011-26,
y por clase de activo (debe mejorar en ≥ 4 de 6 clases en `tx`). Si no, se descarta.
