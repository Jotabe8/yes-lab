# El mejor sistema descartado, recalculado para Darwinex Zero (16-11-2026)

## Resumen

**Ninguno revive en Darwinex.** El mejor descartado del proyecto es el **gotobi del yen** (comprar USDJPY de
08:00 a 09:55 JST los días 5, 10, 15, 20, 25 y fin de mes). Es el efecto más sólido que tenemos fuera del ORB
US100: +0,110 R bruto con t 5,4 en 2003-2026 y la misma ventaja en los 15 años que nunca se habían mirado. Murió
solo por coste. En Darwinex el coste sigue siendo demasiado alto: solo la comisión ya son 0,75 pips, casi
el doble del disparador de 0,8 pips total. El segundo mejor, el ORB GER40, no llega a t 2,4 **ni con coste cero**.
Darwinex sigue siendo solo para el DARWIN del ORB US100.

## 1. Cómo elegí el candidato

Revisé las 98 familias de `metodo/v3/registro_ideas.csv`, más DIARIO.md y las memorias de descartes (oct, nov,
v3-v12, scalping v2). Criterio de siempre: bruto real (t y placebo), que se repita en datos no mirados y que el
motivo del descarte sea algo que Darwinex cambie (coste, swap o reglas de prop).

| Candidato | Prueba de que el efecto es real | Por qué cayó | ¿Lo cambia Darwinex? |
|---|---|---|---|
| **Gotobi USDJPY** | t bruto 5,4; 2003-17 nunca visto t 4,4; placebo +0,01 | coste (2,2 pips brutos frente a 1,4-1,5) | coste distinto: **se recalcula** |
| ORB GER40 | supera placebos, réplica 99,9 %, corr 0 con US100 | t neto 1,58 | FDAX más barato: **se recalcula** |
| ORB cripto | t 2,98 en BTC+ETH | réplica en 8 monedas falla (clase D) y DZ solo tiene MBT | no |
| Subastas del Tesoro | FRED t 2,8-3,9 | en futuros ≈ 0 y apagado desde 2016 | ya probado en ZN de DZ |
| Momentum 12 m, cesta, prima nocturna, tendencia 100/4 | t 2,36-2,37 | swap en FTMO; sin swap son beta | ya probados sin swap para DZ (13-11) |
| ORB JP225 | bruto t 3,3 | coste | DZ no tiene Nikkei |

Las familias que mató el swap de FTMO ya se repitieron con costes de futuros sin swap el 13-11
(`INFORME_DARWINEX_ESTRATEGIAS.md`, `autores-orb`), y ninguna supera a estar siempre comprado. No las repito.

## 2. Gotobi con costes de Darwinex (`recalculo_dz.py`)

Comisión DZ en forex: 0,005 % del nominal ida y vuelta, que son 0,75 pips con el USDJPY a 150. Horquilla a las
23:00 UTC: en FTMO se midió 0,73-0,76 pips. Pruebo tres escenarios.

| Lugar | Coste i/v | Neto R | t | 2018-26 | Costes ×2 | R/año |
|---|---|---|---|---|---|---|
| DZ CFD, horquilla 0,40 (optimista) | 1,15 pips | +0,044 | 2,18 | +0,043 (t 1,2) | −0,021 | 3,2 |
| **DZ CFD, horquilla 0,55 (central)** | **1,30 pips** | **+0,036** | **1,76** | +0,034 (t 1,0) | −0,038 | 2,6 |
| DZ CFD, horquilla como FTMO | 1,55 pips | +0,022 | 1,06 | +0,019 | −0,067 | 1,6 |
| DZ futuros 6J | ~2 pips | −0,004 | — | — | — | — |
| (disparador, no existe en DZ) | 0,8 pips | +0,064 | 3,16 | +0,063 | +0,019 | 4,7 |

- No pasa en ningún escenario: el listón es t ≥ 2,4 y que con costes ×2 siga siendo positivo.
- Como DARWIN propio: Sharpe mensual 0,39 (2018-26), ventanas de 6 meses positivas el 60 % (el ORB tiene 88 %).
  Monte Carlo de 36 meses: mediana +7,8 R y un 25 % de probabilidad de acabar en negativo.
- Mezclado con el ORB US100 a igual riesgo **baja** el Sharpe del DARWIN de 1,38 a 1,24. Con el peso óptimo
  (25 %) sube a 1,43, pero eso es elegir el peso mirando los resultados y no llega a la mejora de +0,10 que pedimos.
- **El disparador del gotobi no se puede cumplir en Darwinex**, porque la comisión sola ya son 0,75 pips. Queda
  cerrado también en DZ.

## 3. ORB GER40 con costes de Darwinex

| Coste | Neto R | t | Costes ×2 |
|---|---|---|---|
| Sin coste (techo) | +0,098 | **2,24** | — |
| DZ FDAX (1 tick + 3 € por orden ≈ 0,0031 %) | +0,081 | 1,85 | +0,064 |
| DZ CFD GDAXI (≈ 0,0055 %) | +0,068 | 1,54 | +0,037 |
| FTMO (0,0052 %) | +0,069 | 1,58 | +0,040 |

Su problema es la señal, no el coste: ni gratis llega a t 2,4. En el DARWIN con el ORB US100 sube el Sharpe de
1,38 a 1,46 (+0,08, por debajo del +0,10 que pedimos), y además tendría que ir en la cuenta de futuros, no en la de CFD.
Según la regla de Jorge (lo que no vale por sí mismo se descarta), no entra.

## 4. Conclusión

- En Darwinex Zero no hay ningún descartado que se pueda rescatar. Lo que mataron el swap y las reglas de prop ya se
  probó sin swap y resultó ser beta. Lo que mató el coste sigue siendo demasiado caro en DZ, o le falta señal.
- Plan sin cambios: el DARWIN de DZ lleva solo el ORB US100 en la cuenta CFD.
- El registro queda así: gotobi cerrado en FTMO y en DZ (en DZ el coste mínimo es 1,15 pips), y el ORB GER40 sigue
  en clase C (t 2,24 incluso con coste cero).

Fuentes de costes: `darwinex/FUTUROS_DZ.md` (tabla de activos de darwinexzero.com, 13-11), `informes/donde_operar/`
(comisión forex de help.darwinex.com), horquilla USDJPY de FTMO medida (`metodo/v10/`).
