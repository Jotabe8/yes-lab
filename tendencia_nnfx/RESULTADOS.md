# Tendencia de largo plazo en forex con gestión NNFX: resultados (14-11-2026)

Reglas fijadas antes de simular en `PREREGISTRO.md` (commit `60bc044`). Código `tendencia_nnfx.py`, salida
completa `salida.txt`, operaciones `ops_V1.csv`, `ops_V2.csv`, `ops_V3.csv`.

**Veredicto: NO PASA. Descartada.** No se escribe el EA.

## Qué se probó

11 pares D1 (MT5, marzo 2005 → mayo 2026). Entrada por ruptura de tendencia larga; gestión NNFX: stop 1,5 ATR,
dos mitades, la primera con objetivo a 1 ATR, después la segunda a BE y salida por el canal contrario de la
mitad de longitud. Coste FTMO real (0,8-2,5 pips) y swap con tipos a 3 meses de cada divisa menos un recargo
de 1,5 %/año.

## Resultados (R por operación, toda la historia)

| Variante | Ops | Bruto | Coste | Swap | **Neto** | t | 2005-15 | 2016-26 | Estrés | Pares + |
|---|---|---|---|---|---|---|---|---|---|---|
| **V1 Donchian 55** (decide) | 1.720 | +0,049 | 0,011 | −0,039 | **−0,001** | −0,04 | +0,066 | **−0,066** (t −2,1) | −0,056 | 4/11 |
| V2 Donchian 100 | 1.207 | +0,037 | 0,011 | −0,044 | −0,017 | −0,46 | +0,077 | −0,102 (t −2,2) | −0,080 | 5/11 |
| V3 cruce SMA 50/200 | 336 | +0,124 | 0,011 | −0,078 | +0,035 | 0,40 | +0,280 | −0,158 (t −2,1) | −0,057 | 8/11 |

Placebos de V1: entrada aleatoria con la misma gestión neto −0,038 R (p95 +0,000; bruto p95 +0,049), lado
contrario neto −0,055 R. V1 queda en el percentil 94 del placebo: justo por debajo del listón.

Criterios de V1: t ≥ 2,4 no; segunda mitad > 0 no; estrés > 0 no; > p95 placebo no; ≥ 7/11 pares no. **0 de 5.**

Sin swap (cuenta swap-free, solo informativo): V1 +0,038 R t 1,26, pero 2016-26 −0,029; V3 +0,113 t 1,18 y
2016-26 −0,118. Tampoco sirve.

## Lectura

1. **La tendencia en forex existió hasta ~2015 y desde entonces no.** Las tres variantes ganan en 2005-2015
   (sobre todo 2008, 2012 y 2014) y pierden en 2016-2026 con t ≈ −2. Es lo que cuenta la literatura del
   momentum en divisas: la prima se ha ido apagando.
2. **El coste no es el problema, el swap sí.** El spread cuesta 0,01 R (stop ancho en D1), pero mantener la
   posición unas 3 semanas cuesta 0,04-0,08 R de swap: se come todo el bruto.
3. **La gestión NNFX no crea ventaja.** La mitad con objetivo a 1 ATR lo toca el 61-63 % de las veces, igual
   que con entradas al azar; el placebo aleatorio con la misma gestión da bruto ≈ 0 (+0,009).
4. Coincide con lo ya descartado (trend following FX D1, torneo NNFX, entrada aleatoria con gestión NNFX). La
   historia larga (21 años, como pedía la auditoría v4) no cambia el veredicto: lo empeora, porque muestra que
   lo poco que había está en la primera mitad.

No se añaden filtros ni capas: con la segunda mitad negativa en las tres variantes, cualquier capa sería
ajustar ruido (como pasó con el forex de 4 capas).
