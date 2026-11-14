# Revisión de descartados con el proceso refinado: resultados (14-11-2026)

Preregistro `PREREGISTRO.md` (commit `d9bc1c9`) y script `analisis.py` (commit `78dcc71`) subidos **antes** de
descargar los datos. Salida completa `salida.txt`; operaciones `gotobi_*_ops.csv`, `eia_ops.csv`.

**Veredicto: ninguna revive.** De 72 familias, solo 2 cumplían las condiciones para reabrir (bruto claro,
veredicto con ventana corta o coste dudoso, historia no mirada disponible). Las dos fallan la prueba
preregistrada. Pero no por lo mismo: el gotobi es un efecto **real y estable durante 23 años** que solo
falla por coste; el EIA era ruido de 2022.

## 1. Triaje

Detalle en `PREREGISTRO.md`. Las candidatas que pidió el coordinador quedan así:

- **ORB GER40, prima nocturna, víspera de festivo:** ya tenían historia larga (14-23 años). Más años no existen
  o no cambian nada. La víspera, además, no es medible con ninguna historia: son ~10 fechas al año comunes a
  todos los índices.
- **ORB cripto y ORB JP225:** el problema es el lugar (coste), no la potencia. Más historia no lo arregla.
- **Carry cripto:** se agotó en 2025. El problema es el presente.
- **Gotobi y EIA:** re-probados. Listón t ≥ 2,64 (Bonferroni para 2 re-pruebas) más el tramo nunca visto.

## 2. Gotobi en el yen: el efecto es real, pero el coste sigue mandando (NO PASA)

| USDJPY (comprar 08:00 → 09:55 JST) | Ops | Bruto R | t bruto | Pips bruto | Neto R (1,41 pips) | t neto |
|---|---|---|---|---|---|---|
| **2003-08 → 2017 (nunca visto)** | 1.043 | **+0,109** | **4,39** | 2,2 | +0,039 | — |
| 2018-26 (el de octubre) | 648 | +0,111 | — | 2,2 | +0,020 | 0,57 |
| Todo 2003-26 | 1.691 | +0,110 | 5,39 | 2,2 | +0,032 | **1,56** |
| Otros días a la misma hora | — | −0,012 | — | — | — | — |

- **Réplica perfecta en 15 años no mirados:** la misma R bruta (+0,109 frente a +0,111) y 18 de 24 años
  positivos. Supera de lejos al placebo (p95 de días no gotobi +0,013 R). Es de los muy pocos efectos del
  proyecto que se sostienen fuera de la muestra en la que se encontraron.
- **Falla por coste:** son 2,2 pips brutos por operación. Con el coste preregistrado (horquilla Dukascopy a
  las 08:00 JST en 2023-26 ≈ 1,1 pips + comisión 5 $/lote) el neto es +0,032 R con t 1,56, y con costes ×2 pierde.
- Las réplicas EURJPY y GBPJPY tienen bruto (t 4,0 y 3,6 en total), pero su horquilla (2,1 y 4,1 pips) se lo
  come entero, y en el tramo nunca visto su t bruto es 1,8-2,0. Criterio de réplica no cumplido.

Criterios: t neto ≥ 2,64 **no**; nunca visto bruto t ≥ 2 sí; nunca visto neto > 0 sí; 2018-26 neto > 0 sí;
costes ×2 > 0 **no**; > placebo sí; réplica en otro cruce **no**. **4 de 7.**

**Coste con el que pasaría** (informativo; no cambia el veredicto):

| Coste total ida y vuelta | Neto R | t | Costes ×2 |
|---|---|---|---|
| 0,6 pips | +0,076 | 3,71 | +0,042 |
| 0,8 pips | +0,064 | 3,16 | +0,019 |
| 1,0 pips | +0,053 | 2,60 | −0,004 |
| 1,4 pips (el preregistrado) | +0,030 | 1,48 | −0,050 |

Disparador de reapertura: **coste total medido ≤ 0,8 pips** (horquilla + comisión) en USDJPY a las 08:00 JST en
un lugar real. La v3 midió que Dukascopy exagera la horquilla de Asia 1,6-1,9× en índices, así que no es
imposible, pero la comisión de FTMO sola ya son 0,35-0,5 pips. Medirlo cuesta poco: la horquilla real de
USDJPY en el MT5 de FTMO entre las 23:00 y las 23:05 UTC de los últimos meses.

Aunque pasara, sería un complemento pequeño: con 0,8 pips da unos 4-5 R al año (72 operaciones), frente a unos
25 R del ORB US100. El peor bache bruto fue de −15 R.

## 3. Deriva tras el inventario EIA: era ruido (NO PASA)

| USOIL, miércoles 10:35 → 14:30 NY | Ops | Bruto R | t bruto | pb | Neto R (5,3 pb) |
|---|---|---|---|---|---|
| **2011-09 → 2020 (nunca visto)** | 446 | +0,055 | **1,24** | — | +0,008 |
| 2021-26 | 301 | +0,031 | — | — | −0,007 |
| Todo | 747 | +0,045 | 1,38 | 7,6 | +0,002 (t 0,05) |

No supera al placebo de dirección al azar (p95 +0,053 R), y los años buenos (2015, 2020, 2022-23) fueron años
de petróleo muy volátil. Los +33 pb de 2021-22 eran ruido. **1 de 7 criterios** (supera a los otros días de la
semana). Descartado del todo, sin disparador.

## 4. Lo que deja esto

- La sospecha de Jorge era razonable, pero en este registro casi no hay descartes injustos por ventana corta:
  las ideas con bruto claro ya se habían probado con historia larga (GER40, prima nocturna, víspera), o las
  frenaba el lugar o la regla, que la historia no arregla.
- El fallo de la ventana corta afectaba sobre todo a **aceptar** (el ORB habría caído con 5 años), no a los
  descartes: casi todos los descartes eran de clase A (sin bruto), y eso se ve bien con 5 años.
- El gotobi pasa de "efecto dudoso" a **efecto confirmado sin lugar barato**, igual que el ORB cripto. Las dos
  esperan lo mismo: un lugar con coste bajo. Es el único hilo pendiente que sale de esta revisión.
- Se han hecho 2 re-pruebas. No hay más candidatas que cumplan el triaje; repetir con otras variantes sería
  justo el sesgo que se quería evitar.
