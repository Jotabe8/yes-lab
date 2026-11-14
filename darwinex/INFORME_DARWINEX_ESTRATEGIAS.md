# Estrategias para Darwinex Zero (13-11-2026)

> **Corrección (13-11, tarde):** la lista real de futuros de Darwinex Zero (`FUTUROS_DZ.md`) **no tiene BTC estándar ni ETH**,
> solo el micro MBT (3 $ por orden ≈ 0,19 R). El CFD de cripto cobra 0,05 % por orden. **El ORB cripto no es operable en
> Darwinex** y la recomendación de la cuenta de futuros queda anulada: se usa la cuenta CFD con el ORB US100 solo. Lo demás
> de este informe (momentum y cesta descartados) sigue igual.

## Resumen

**Hay un segundo sistema operable, y es Darwinex el que lo hace operable:** el ORB cripto de la apertura de
Nueva York (BTC + ETH en futuros CME estándar). Ya pasó su prueba preregistrada (t 2,98, correlación 0,08 con
el ORB US100), pero en FTMO no cabía: un contrato arriesga ~1.800 $ y las cuentas de futuros prop solo permiten
perder 2.000-4.500 $. La cuenta de futuros de Darwinex Zero tiene **1 M$ virtuales y no tiene pérdida máxima**:
un contrato es el 0,18 % de la cuenta. Es justo el disparador que dejamos anotado para reabrirlo.

**Las familias que mató el swap de FTMO no reviven en Darwinex.** El momentum multiactivo (una sola prueba,
2005-2026, costes de futuros sin swap) se queda en t 2,37 y **por debajo** de estar siempre comprado. La cesta
siempre comprada es beta: Sharpe 0,71, pero mezclada con el ORB solo sube su Sharpe de 1,38 a 1,46.

**Recomendación:** contratar en Darwinex Zero la **cuenta de futuros** (no la de CFD) y correr en el mismo
DARWIN el ORB US100 (sobre el NQ) y el ORB cripto (BTC y ETH). En 2021-26 el Sharpe mensual del DARWIN pasa
de 1,33 a 1,72 y las ventanas de 6 meses positivas, de 94 % a 98 %.

## 1. Qué cambia en Darwinex Zero (verificado en la web el 13-11-2026)

| Concepto | Dato | Fuente |
|---|---|---|
| Tipos de cuenta | CFD (MT4/MT5, 100 K$), cripto CFD (1:1), **futuros CME y Eurex (MT5, 1 M$)**, acciones y ETF de EE. UU. al contado (sin apalancamiento) | documentación DZ |
| Precio | CFD 45 €/mes; futuros 56 $/mes (incluye 6 $ de datos); cripto CFD 50 $/mes. Cada tipo es una suscripción y un DARWIN aparte | mypropgenius 2026 |
| Futuros | "60+ contratos", vía Interactive Brokers. **No se publica la lista ni la comisión** | help.darwinex.com |
| Swap | Índices CFD: diario a las 17:00 NY, triple el miércoles; las tarifas no se publican. Los futuros no tienen swap | darwinex.com/spreads |
| Comisión forex/materias primas CFD | ~0,005 % del nocional por orden | help.darwinex.com |
| Rating DarwinIA | 67 % retorno de 6 meses, 22 % retorno del mes, 11 % DD máximo de 6 meses; sin penalización por correlación con el mercado | documentación DZ |

Como Darwinex reescala cada DARWIN a un VaR objetivo, **lo que puntúa es el retorno por unidad de riesgo
(Sharpe) y que las ventanas de 6 meses salgan positivas**, no el riesgo por operación.

## 2. Candidatas y veredicto

| Candidata | Por qué parecía posible | Resultado | Veredicto |
|---|---|---|---|
| **A. ORB cripto 9:30 NY (BTC + ETH, futuros CME estándar)** | Edge ya probado; solo faltaba un lugar donde cupiera | 2021-26: +0,195 R/día, t 2,98; costes ×2 t 2,3; corr con ORB US100 0,08; Sharpe 1,24 (2024-26: 0,98) | **Pasa. Operable en DZ futuros** si están los contratos BTC y ETH de CME |
| B. Momentum 12 meses multiactivo (25 mercados) | Lo mataba el swap de FTMO | Neto 5,4 %/año a 10 % de vol, Sharpe 0,51, **t 2,37**; 2ª mitad 2,7 %/año; **−2,5 %/año frente a estar siempre comprado** | Descartada (clase D: no supera al placebo) |
| C. Cesta siempre comprada (índices, forex, metales) | IndexBasket, oro y cripto cesta: beta barata sin swap | Sharpe 0,71 (2005-26), pero con el ORB solo sube el Sharpe de 1,38 a 1,46 (el umbral era +0,10) | Descartada (beta, no ventaja; no mejora el DARWIN) |

Preregistro: `PREREGISTRO_DZ.md` (commit `92fea33` en yes-lab, antes de ejecutar B y C). Código: `tsmom_dz.py`,
`dz_combinado.py`. La tendencia 100/4 con trailing ya cayó en cuenta sin swap el 30-10 (por debajo del placebo
fuera de muestra); B es la versión de cartera de esa misma familia y confirma lo mismo.

## 3. El DARWIN de futuros: ORB US100 + ORB cripto

Monte Carlo de 36 meses (el mismo de `darwinex-senales/dz_sim.py`: bloques de 3 meses, rating aproximado,
DarwinIA mínima de 30.000 €, comisión 15 % con HWM). Ventana común 2021-03 → 2026-10. La mezcla se pone a
igual riesgo y luego al mismo VaR que el ORB solo.

| DARWIN | Sharpe mensual | DARWIN/año | Neto €/año solo DarwinIA | Neto €/año + permanente 100K (+10 %) | 36 meses en negativo |
|---|---|---|---|---|---|
| ORB US100 solo, cuenta CFD (35 €/mes) | 1,33 | +19,8 % | +554 € | +2.620 € | 23 % / 4 % |
| **ORB US100 + cripto, cuenta futuros (50 €/mes)** | **1,72** | **+27,4 %** | **+962 €** | **+3.934 €** | **10 % / 0,5 %** |

- 2021-26 es una ventana buena para el ORB US100 (con 2018-26, el informe anterior daba +310 y +1.800 €/año para
  el ORB solo). Lo que vale es la diferencia: **unos +400 €/año sin permanente y +1.300 €/año con ella.**
- El ORB cripto se ha debilitado en BTC (2025: +0,02 R; 2026: +0,04 R). ETH sigue bien (+0,32 y +0,13).
  Es el riesgo principal: si en 2027 sigue así, el ORB cripto aporta poco.

## 4. Siguiente paso hacia el EA

1. **Antes de pagar:** comprobar que la cuenta de futuros de DZ lista los contratos **BTC (5 BTC)** y **ETH
   (50 ETH)** de CME, y la comisión por contrato. Los micros (MBT, MET) no sirven: su comisión se come el edge.
   También el **NQ** o el MNQ, para el ORB US100. Basta con preguntarlo al soporte o mirarlo en la prueba gratuita.
2. **EA ORB_CRIPTO_v100.mq5:** mismas reglas que la simulación. Rango 9:30-9:40 NY, lado del cuerpo de la vela si
   es ≥ 10 % del rango, entrada a las 9:40, stop 0,15 × ATR14 de la sesión 9:30-16:00, salida a las 15:55, de lunes
   a viernes. BTC y ETH a igual riesgo. En 1 M$, unos 0,35 % por R y estrategia: ~2 contratos BTC y ~4 ETH.
3. **Strategy Tester:** el historial de futuros del MT5 de DZ puede ser corto; el cruce con Python se hace con
   lo que haya (objetivo: mismo lado ≥ 95 % de los días y R medio ±20 %).
4. **ORB US100 en NQ:** adaptar el v018 al tamaño de contrato del futuro (1 R ≈ 800-1.200 $ por NQ).

## Fuentes

- Tipos de cuenta y activos: https://darwinexzero.document360.io/docs/trading-accounts-assets
- Apalancamiento y capital virtual: https://darwinexzero.document360.io/docs/darwinex-zero-leverage
- DZ frente a Darwinex: https://darwinexzero.document360.io/docs/en/darwinex-zero-versus-darwinex-classic
- Rating DarwinIA: https://darwinexzero.document360.io/docs/rating
- Costes de ejecución: https://help.darwinex.com/execution-costs
- Swaps y dividendos de índices: https://darwinex.com/spreads
- Futuros vía Interactive Brokers: https://help.darwinex.com/assets-available
- Precios por tipo de cuenta: https://mypropgenius.com/reviews/darwinex-zero/
