# Pata diversificadora para el DARWIN del ORB US100 (16-11-2026)

## Resumen

**Descartada por el preregistro.** La única pata realmente descorrelacionada del ORB que se puede operar en Darwinex
Zero es la **paridad de riesgo simple en futuros (ES + ZN + GC a igual riesgo, 10 % de vol, rebalanceo mensual)**.
Su correlación con el ORB es 0,02 y sube el Sharpe del DARWIN de 1,04 a 1,20 en 2018-26. Pero:

1. **Empeora el peor drawdown** (27,3 R → 30,5 R, por 2022), que era una de las condiciones fijadas antes.
2. **Toda la mejora viene de la prima de la pata, no de que cubra al ORB.** En los peores meses del ORB la pata gana lo
   mismo que en los demás (+0,53 % frente a +0,54 %). Con media cero, el DARWIN baja a 0,93. **Con la prima a la mitad**
   (lo razonable fuera de muestra para acciones y bonos), **la mejora desaparece**: 1,04 → 1,06.
3. Obliga a la cuenta de futuros (50 €/mes frente a 35) y a portar el ORB al NQ. En euros, con la prima histórica gana
   unos +65 €/año sin permanente (+415 con permanente +10 %); con la prima a la mitad, −60 / +35 €/año.

Es lo que esperaba la teoría: una pata beta con Sharpe S y correlación 0 suma como mucho √(1,04² + S²) − 1,04. Con S
de 0,6 eso son +0,16; con 0,3, +0,04. Mientras no haya un segundo sistema con ventaja propia, el DARWIN sigue con el
ORB US100 solo en la cuenta CFD.

## Qué se probó (preregistro `PREREGISTRO.md`, commit `0db46b5`, antes de bajar los datos)

- Datos: futuros continuos de Yahoo (bajados con `datos-diversificadora.yml`); los saltos de roll se sustituyen por el
  sustituto al contado (^GSPC, XAUUSD de Dukascopy, DGS7). Costes 2 pb por giro y por roll.
- Combinación con peso fijo (vol de la pata = 0,5 × vol del ORB) y la mezcla reescalada a la vol del ORB, porque
  Darwinex reescala a VaR objetivo. ORB = serie v018 BE − 0,05 R por operación, mensual 2018-01 → 2026-10.

## Resultados

### Pata sola (neta)

| Periodo | Ret/año | Vol | Sharpe | t | Peor DD |
|---|---|---|---|---|---|
| 2003-2026 | 9,2 % | 10,4 % | 0,89 | 4,33 | 19 % |
| 2003-2011 | 13,4 % | 10,5 % | 1,28 | 3,83 | 14 % |
| 2012-2017 | 7,2 % | 10,1 % | 0,72 | 1,75 | 12 % |
| **2018-2026** | **6,4 %** | 10,6 % | **0,61** | 1,80 | 19 % (2022: −15 %) |

El Sharpe cae a la mitad década a década (el viento de cola de los bonos se acabó). Con el sustituto al contado sin
limpiar rolls sale algo peor: 0,76 en 2003-26 y 0,56 en 2018-26.

### DARWIN 2018-26 (en R del ORB, todo a la misma volatilidad)

| | Sharpe | Peor DD | 6 m positivas | VaR 95 % mensual |
|---|---|---|---|---|
| ORB solo | 1,04 | 27,3 R | 73 % | 10,3 R |
| **ORB + P (peso fijo 0,5)** | **1,20** | **30,5 R** ✗ | 80 % | 9,8 R |
| ORB + P con prima a la mitad | 1,06 | 32,2 R | 77 % | 10,2 R |
| Placebo: ORB + P con media cero | 0,93 | 33,9 R | 73 % | 10,5 R |
| (informativa) ORB + P4 con CL y HG | 1,22 | 23,9 R | 79 % | 9,3 R |

### Criterios

| # | Criterio | Resultado | |
|---|---|---|---|
| 1 | Pata sola t ≥ 2 (2003-26) y Sharpe 2018-26 > 0 | t 4,33; 0,61 | ✓ |
| 2 | Correlación mensual con el ORB ≤ 0,20 | +0,02 | ✓ |
| 3 | ΔSharpe ≥ +0,10, peor DD no peor, 6 m positivas no menos | +0,16; **DD 27,3 → 30,5 R**; 73 → 80 % | **✗** |
| 4 | Con prima a la mitad, Sharpe > ORB solo | 1,06 > 1,04 (por la mínima) | ✓ |
| 5 | Bootstrap 3 meses P(ΔSharpe > 0) ≥ 80 % | 89 % (p10 −0,01) | ✓ |
| 6 | Monte Carlo €/año mezcla en futuros > ORB solo en CFD | 378 > 312; con permanente 2.221 > 1.807 | ✓ |

Controles: con desfases aleatorios de la pata el ΔSharpe mediano es +0,17 y el real queda en el percentil 42, o sea que
la baja correlación no es suerte, pero tampoco hay cobertura: cualquier serie independiente con esa prima daría lo mismo.
En 2012-26 con la réplica del ORB la mezcla sube de 0,85 a 1,06 y el DD mejora (38 → 34 R); P4 lo empeora (38 → 41 R).
El DD de un único camino cambia de signo según la ventana: es ruido, y lo robusto es que la ganancia depende de la prima.

### Monte Carlo de 36 meses (`dz_sim`, mismos supuestos de los informes anteriores)

| DARWIN | Neto €/año | + permanente +10 % | P(neg) 36 m |
|---|---|---|---|
| ORB solo, cuenta CFD (35 €/mes) | 312 | 1.807 | 38 % / 13 % |
| ORB + P, cuenta futuros (50 €/mes) | 378 | 2.221 | 37 % / 10 % |
| ORB + P prima a la mitad, futuros | 254 | 1.842 | 44 % / 14 % |

### Tamaño en la cuenta de futuros

Con 1 M$ y la pata a 10 % de vol: 1 ES, 8 ZN y **0,5 GC**. A la mitad de la vol del ORB (0,45 % por R) serían 0,65 ES y
0,3 GC: no se puede. Haría falta subir el ORB a ~1,4 % por R (10-15 NQ) y la pata a 2 ES, 16 ZN y 1 GC, y dejar que
Darwinex reescale. Otro coste práctico más.

## Por qué no se probaron otras patas

- Tendencia/momentum multiactivo y cesta siempre comprada: ya probadas sin swap el 13-11 (`INFORME_DARWINEX_ESTRATEGIAS.md`).
- En la cuenta CFD cualquier pata de varios días paga swap (NDX largo −45 $/día por contrato, ~6,5 %/año del nominal).
- Carry de divisas con 6A-6S: prima publicada menor (Sharpe ~0,3-0,4) y con caídas en los mismos momentos que la bolsa;
  por la cuenta de arriba sumaría ≤ +0,05 de Sharpe.
- Gotobi, ORB GER40, oro en Asia, subastas: ya recalculados para DZ (`mejor_descartado/`, `NUEVAS_VIAS_DARWINEX.md`).

## Qué haría falta para reabrirlo

Un segundo sistema con ventaja propia (Sharpe ≥ 0,6 fuera de muestra) y correlación baja con el ORB. Una pata beta
solo merece la pena si Jorge decide aceptar conscientemente beta en el DARWIN; en ese caso la versión defendible es
P (ES + ZN + GC), pero con la prima esperada de hoy el beneficio esperado es casi cero y añade el riesgo de un 2022.

Código: `diversificadora.py` (salida en `salida.txt`). Datos: `datos_diversificadora/` (Yahoo, workflow
`datos-diversificadora.yml`), `datos_bonos/`, `datos_oro/`.
