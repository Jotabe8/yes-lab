# Segunda ronda de ideas: reglas fijadas antes de mirar los datos

Fecha: 2026-10-25. Jorge eligió seguir buscando sistemas distintos del ORB. Este archivo se
sube al repositorio antes de ejecutar ninguna de las tres pruebas. Cada idea se valida una sola
vez con la regla de aquí; no se reajusta. Nada de esto es una recomendación de inversión.

Periodos para las tres: dentro de muestra hasta 2019-12-31 (2018-2019 si solo hay datos M1),
fuera de muestra desde 2020-01-01. Criterio común: media neta fuera de muestra > 0 con t > 2 y
media neta dentro de muestra > 0. Se publican también el resultado bruto y con costes al doble.

## A. Rebalanceo de coberturas a fin de mes en forex (Melvin y Prins, 2015)

**Hipótesis.** Los inversores extranjeros con acciones de EE. UU. cubren el dólar y reajustan la
cobertura en el fixing de fin de mes. Si la bolsa de EE. UU. ha subido más que la extranjera en
el mes, tienen más dólares que cubrir y venden dólares a plazo: el dólar se debilita en los
últimos días del mes. Al revés si la bolsa extranjera ha ido mejor.

**Datos.** Dukascopy D1 2010-2025.

| Par | Índice extranjero | Dirección si EE. UU. ha ido mejor |
| --- | --- | --- |
| EURUSD | EU50 (EUSIDXEUR) | largo EURUSD |
| GBPUSD | UK100 (GBRIDXGBP) | largo GBPUSD |
| AUDUSD | ASX 200 (AUSIDXAUD) | largo AUDUSD |
| USDJPY | Nikkei (JPNIDXJPY) | corto USDJPY |

**Regla.** Al cierre de la antepenúltima sesión del mes (tres antes del final) se compara el
retorno del US500 desde el último cierre del mes anterior con el del índice extranjero, ambos en
moneda local. Se entra en la apertura siguiente en la dirección de la tabla y se sale al cierre
de la última sesión del mes. Una operación por par y mes.

**Costes.** 0,01 % por lado (0,02 % por operación) más 0,01 % por noche de financiación.

## B. Prima nocturna de la bolsa de EE. UU. (Cliff, Cooper y Gulen, 2008; Lou, Polk y Skouras, 2019)

**Hipótesis.** Casi toda la rentabilidad de los índices de EE. UU. llega entre el cierre y la
apertura de la sesión de contado; durante la sesión el retorno medio es casi cero.

**Datos.** M1 de US500 (Dukascopy) y US100 (FTMO) del PC de Jorge, 2018-2026.

**Regla.** Largo desde el último minuto de la sesión de contado (16:00 Nueva York) hasta el
primer minuto de la siguiente (09:30 Nueva York), de lunes a jueves. El viernes no se opera,
porque la cuenta fondeada Standard de FTMO no deja mantener posiciones el fin de semana.

**Costes.** 0,02 % por operación (spread de entrada y salida) más 0,015 % por noche de swap
(alrededor del 5,5 % anual).

## C. Estacionalidad horaria del oro

**Hipótesis.** El oro tiende a subir fuera del horario de Londres y Nueva York y a bajar en el
fixing de Londres (Caminschi y Heaney, 2014, documentan la caída alrededor del fixing de la
tarde). La forma que se prueba es la más simple: largo en la sesión asiática.

**Datos.** M1 de XAUUSD (Dukascopy) del PC de Jorge, 2018-2026.

**Regla.** Largo desde las 17:00 de Nueva York (cierre del día de metales) hasta las 08:00 de
Londres, de lunes a jueves.

**Costes.** Spread real de la vela de entrada y salida (columna `spread` de Dukascopy) más
0,01 % por noche de swap.
