# v10 (15-11-2026): datos nuevos y un sitio más barato

Pedido de Jorge: centrar la búsqueda en las dos vías que dejó abiertas la v9, (a) datos de verdad nuevos y
(b) un sitio más barato para las ventajas brutas que el coste se come.

## Resumen

| Vía | Qué se hizo | Resultado |
|---|---|---|
| Sitio barato: gotobi (único disparador de coste que seguía abierto) | Horquilla real de USDJPY medida en Dukascopy M1 bid/ask 2018-26 (PC de Jorge) a las 08:00 y 09:55 JST | Horquilla 0,7-1,1 pips a las 08:00 y 0,5-0,8 a las 09:55 en 2022-26 (media 0,99 y 0,52). Coste de horquilla ≈ 0,76 pips, igual que en FTMO. En IBKR: 0,6 de comisión + 0,76 ≈ **1,35 pips**, no 0,9. Disparador (≤ 0,8) **imposible**: solo la horquilla ya llega a 0,76. **Cerrado.** |
| Sitio barato: resto | Revisado DONDE_OPERAR (14-11) | Nada pendiente: ETH cerrado por la réplica (v6), BTC y JP225 sin ventaja en 2024-26, GER40 sin ventaja en ningún sitio, víspera con 9 ops/año. Al ORB US100 el coste no le importa. **La vía del sitio barato queda agotada.** |
| Datos nuevos | Fuentes revisadas (abajo) | La única que abre hipótesis nuevas que pasan T0 y caben en el presupuesto es **Databento** (pago por uso, 125 $ gratis al darse de alta). |
| Datos nuevos: pruebas | Preregistro `PREREGISTRO_V10.md`, descarga con tope de coste `descargar_databento.py` + `v10-databento.yml`, análisis `analizar.py` (probado con datos sintéticos) | **Pendiente de la clave de Databento de Jorge.** |

## Fuentes de datos nuevas

| Fuente | Qué da que no tengamos | Coste | ¿Hipótesis que pase T0? |
|---|---|---|---|
| **Databento XNAS.ITCH `imbalance`** | Desequilibrio de las subastas de apertura y cierre de Nasdaq (NOII), cada 10 s de 9:25 a 9:28 y cada segundo hasta las 9:30; igual de 15:50 a 16:00 | Pago por GB; 9 valores × 8 años son unos cientos de MB → dentro del crédito gratis (se confirma con la API antes de bajar) | **Sí (H1)**: el flujo obligado de la apertura, justo donde vive la ventaja del ORB |
| **Databento GLBX.MDP3 `trades`** | Operaciones del NQ con el lado agresor (volumen con signo, "delta") | Solo la ventana 9:30-9:40 de cada día; estimado dentro del crédito | **Sí (H2)**: ¿el ORB falla cuando el flujo va contra la vela (absorción)? |
| Databento imbalance de cierre (MOC) | Desequilibrio de las 15:50 | Viene en la misma descarga | Casi no: la propia Nasdaq mide que el 80 % del movimiento se descuenta en 300 ms y que el efecto medio es 5,5 pb por acción. Se prueba (H3) solo porque es gratis |
| Libro de órdenes completo NQ (MBP-10/MBO) | Profundidad del libro | Caro (decenas de GB al año) | No: las ventajas del libro duran segundos, imposibles con MT5 |
| Opciones por precio de ejercicio (ThetaData, ORATS, Cboe) | Gamma por strike | 30-100 $/mes | No: el GEX de SqueezeMetrics ya falló por potencia (v5, clase C); más detalle no da más operaciones |
| Alpaca / Polygon (acciones SIP) | Barras y operaciones de acciones | Gratis / 29 $/mes | No para prop: ninguna firma con bots opera acciones pequeñas (small caps parado en P0) |
| CME DataMine, CFTC, FRED, calendario | Ya usados o caros | — | Agotados en v3-v9 |

Todas las fuentes de pago están bloqueadas desde el contenedor y desde el PC de Jorge (probado hoy:
hist.databento.com, data.alpaca.markets, polygon). La descarga va por GitHub Actions, como las demás.

## Las tres hipótesis preregistradas (detalle y listón en `PREREGISTRO_V10.md`)

- **H1a**: el ORB v018 gana más los días en que el desequilibrio de apertura agregado (QQQ + 8 mayores del
  Nasdaq-100, último mensaje antes de las 9:30) va en la dirección de la vela del rango. **H1b**: el desequilibrio solo,
  como sistema en NQ de 9:31 a 9:59.
- **H2a**: el ORB gana más cuando el delta del NQ en 9:30-9:40 va con la vela que cuando va contra ella. **H2b**: más
  delta, más R.
- **H3**: desequilibrio de cierre → NQ de 15:51 a 15:59.

Lo que haría falta para operarlas si pasan:
- H2a sí es operable sin pagar datos: el delta sale del propio feed de futuros. Encaja con el port a NinjaTrader
  (Lucid Flex 50K con MNQ) que ya está validado. En MT5/CFD no hay delta real.
- H1a y H1b necesitan el desequilibrio en vivo: Databento en vivo cuesta 199 $/mes, fuera del presupuesto salvo
  que la mejora fuese grande.

## Qué tiene que hacer Jorge (5 minutos)

1. Crear cuenta en databento.com (da 125 $ de crédito, caduca a los 6 meses).
2. Copiar la API key del portal y guardarla en GitHub: repo yes-lab → Settings → Secrets and variables → Actions →
   New repository secret, nombre `DATABENTO_API_KEY`.
3. Avisar en el hilo. Primero se lanza en modo `coste` (pregunta el precio a la API, gratis) y solo se baja si el
   total es ≤ 100 $.

## Archivos
`PREREGISTRO_V10.md`, `descargar_databento.py`, `analizar.py`, `MODO`, `serie_v018_be.csv`,
`horquilla_usdjpy.py` y `horquilla_usdjpy_salida.txt`; workflow `.github/workflows/v10-databento.yml`.
