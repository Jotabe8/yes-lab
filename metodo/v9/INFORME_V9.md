# Búsqueda v9 (14-11-2026 noche): información fuera del precio

Pedido: seguir buscando un segundo sistema descorrelacionado del ORB US100, priorizando calendario, flujos
obligados y datos macro. Se revisaron antes las ~90 familias del registro y las notas de descartes.

## Resumen

| # | Familia | Fuente de información | Paso | Resultado | Clase |
|---|---|---|---|---|---|
| A | Ruptura en el instante del dato (NFP, IPC, FOMC) en oro, 3 divisas, US100, US500, 2011-26 | Calendario BLS/Fed | Prueba preregistrada | Bruto +0,000 R (t 0,00), neto −0,12 R; evento − placebo t 0,15 | A |
| B | El dólar cae tras el fix del BCE (Krohn-Mueller-Whelan) | Flujo de clientes en los fixes | Prueba preregistrada | Bruto +0,04 pb (t 0,07); 2020-26 negativo; solo EURUSD ≈ coste | A |
| — | Prima del día de anuncio (Savor-Wilson) | Calendario macro | T0 | 182 años necesarios | C |
| — | Subasta del Tesoro 13:00 en ZN (Darwinex) | Calendario del Tesoro | T0 | Margen: efecto ≈ coste | C |
| — | US100 ante subastas de 10/30 años | Calendario del Tesoro | T0 | 24 ops/año, efecto mínimo | C |
| — | Día de la semana; quincena/día de paga | Calendario | T0 | Sin efecto vivo / 273 años | C |
| — | Sol en Nueva York; ciclo lunar | Meteorología / calendario | T0 | Efectos de 1-3 pb/día | C |
| — | Liquidación del VIX (miércoles) | Calendario de opciones | T0 | 12 ops/año | C |
| — | Hueco de fin de semana BTC-CME; prima Coinbase/Kimchi; emisiones de Tether | Otros mercados / cadena | T0 | Coste cripto ≥ efecto | C |
| — | Estacionalidad transversal de materias primas (Darwinex) | Estacionalidad de otros mercados | T0 | 66 años necesarios | C |
| — | Almacén de gas EIA (NG) | Dato semanal | T0 | Incorporación inmediata, margen | C |
| — | Liquidez neta de la Fed (TGA/RRP); put/call CBOE | Datos macro / opciones | T0 | Más de 400 años | C |
| — | Flujos NISA; compras de ETF del BoJ | Flujos obligados Japón | T0 | 2 años de historia / programa terminado | C |
| — | Reversión al cierre en acciones (Baltussen-Da-Soebhag 2025); estacionalidad en opciones (Bali et al.) | Literatura reciente | T0 | No operables en FTMO ni Darwinex | — |

**Nada pasa P1.** Ninguna de las dos pruebas tiene siquiera ventaja bruta.

## Lo que deja claro esta tanda

1. **La primera vela tras un dato importante no predice nada** en ningún mercado (ni en oro ni en divisas ni en
   índices), al contrario que la primera vela de la apertura del US100. La ventaja del ORB no es "información
   nueva", es algo propio de la apertura de contado de Nueva York.
2. **Los flujos en los fixes de divisa ya están arbitrados**: lo que queda (≈1 pb en EURUSD) es igual al coste.
3. **Con el triaje T0, casi todo el espacio de ideas "fuera del precio" cae antes de mirar datos**: los efectos de
   calendario publicados tienen pocas operaciones al año o pocos pb por día, y necesitan décadas de datos para
   distinguirse del ruido. Lo único que pasaba el T0 (la ruptura en el dato) era una apuesta sin artículo detrás.

## Recomendación

Con v3-v9 (≈110 familias y ~20 pruebas preregistradas) el patrón es estable: solo el ORB US100 tiene ventaja
neta operable. La diversificación útil sigue siendo de cuentas, firmas y tiempo (plan de cuentas vigente), no de
estrategias. Reabrir la búsqueda solo con **datos nuevos de verdad** (libro de órdenes real de futuros,
desequilibrios MOC, posiciones de opciones por precio de ejercicio) o con un **lugar más barato** para las clases B.

## Archivos

`PREREGISTRO_EVENTOS.md`, `eventos.csv`, `eventos.py`, `analizar_a.py`, `salida_a.txt`, `RESULTADOS_A.md`,
`PREREGISTRO_FIX_USD.md`, `fix_usd.py`, `salida_fix_usd.txt`, `RESULTADOS_B.md`, `T0_TANDA1.py`, `T0_tanda1_salida.txt`.
Datos: `datos/` (M1 07:00-17:00 NY y diario de 6 mercados 2011-26, workflow `v9-eventos.yml`).
