# Validación del ORB US100 v019 (tope de 21 días sin operar) con las pruebas del PR #36 — 14-11-2026

**Versión probada:** `ORB_US100_AGR_v019.mq5` de `Prop Firm Challenges\ea_v019\` (v018 + `InpVolMaxPauseDays = 21`,
`InpVolPauseRiskMult = 0,25`). Es la que está compilada en el `MQL5\Experts` de la cuenta real (67.720 B, .ex5 de las
18:17 Madrid). La otra «v019» (`probar_mt5\`, v018 + nº de cuenta en el CSV) se guarda en
`Experts\_backup_v019_antiguo_20261114\`; su test de MT5 es idéntico byte a byte al de la v018.

## Resultado

| Prueba | Resultado | Veredicto |
|---|---|---|
| P1 paseo aleatorio (20 réplicas, `sinteticos.velas_paseo`, FTMO M1 2021-09 → 2026-10) | R bruta **+0,005** (t 0,42, 20.836 ops; coste medio 0,019 R) | **Pasa** |
| P5 réplica Python frente a Strategy Tester v019, sin simulador (R puro, 2022-01 → 2026-11-05) | 983 de 986 emparejadas; R media +0,177 / +0,174; corr 0,998; 98 % con \|ΔR\| ≤ 0,10 | **Coinciden** |
| P5 réplica frente al tester con simulador de fases (v019_test_tope21) | 954 de 965; corr 0,998 | Coinciden |
| Operaciones forzadas por el tope | Tester 6 (7 avisos, uno cae en día doji): 10-02, 16-03, 25-05-2022, 15-08-2024, 24-04-2025, 01-07-2026. Python: las mismas salvo 14-08-2024 en vez de 15-08 | Coinciden |
| Pausa más larga 2022-26 | 22 días en los dos (v018: 34) | — |
| Cuenta real FTMO 14-10 → 06-11 (v017, mismas reglas sin filtro) | 14 de 14 ops reales con el mismo día y lado; R real 0,02 R peor de media (deslizamiento) | Coinciden, salvo el 20-10 |

Comprobado también: el paseo aleatorio da lo mismo con la v018 (+0,005) y sin filtro de volatilidad (+0,004). El
motor no fabrica ventaja; el +0,186 R bruto de los datos reales no sale del código.

## Operaciones que no coinciden y por qué

**Tester sin simulador (3 + 3 sin pareja):** todas son casos al filo de una regla, con velas del símbolo del tester
que difieren ~1 punto del CSV (comprobado en `datos/velas_tester_dudosas.csv`):
- 16-04-2024 (solo MT5): cuerpo/rango 8,5 % en el CSV, por encima del 10 % en el tester.
- 25-07-2024 (solo MT5): percentil de volatilidad 90,08 en Python (bloquea), por debajo de 90 en MT5.
- 14-08 / 15-08-2024: consecuencia de la anterior. MT5 operó el 25-07 y su cuenta de 21 días empieza un día más tarde.
- 04-09-2024 y 06-08-2025 (solo Python): cuerpo del 10,1 % y 11,1 %, justo en el límite.

**Pares con |ΔR| > 0,1 (22 de 983):**
- 11 son días de cierre anticipado de la bolsa USA de 2022-23 (Presidents' Day, 4 de julio, Acción de Gracias...)
  y dos huecos de datos (27-06 y 07-07-2022). La lista de festivos del EA empieza en 2024, así que en el tester la
  posición se queda abierta hasta la apertura del día siguiente (01:05). En vivo no pasa (2024-27 están en la lista),
  pero **hay que ampliar la lista antes de 2028**.
- 8 son salidas por trailing con unos minutos de diferencia (el tester genera 4 ticks por vela M1, paso de 0,1 R).
- 17-09-2025 (FOMC): el stop del corto quedó a 0,08 puntos del máximo; MT5 lo tocó con una entrada 0,10 más baja.
- 07-02-2025: hueco de 46 puntos a las 17:00. Python sale a la apertura (−1,48 R); el tester llena en el stop
  (−1,00 R). **El tester es optimista con los huecos dentro de la sesión**; la cuenta real llenaría como Python.

**Cuenta real:**
- 20-10-2026: la réplica y el tester abren un corto (−1 R) y la cuenta no operó. No he podido leer el log de ese
  día (no está en `MQL5\Logs` y la lectura de las otras carpetas del terminal real se denegó). Si se copia el
  log a `estado_mt5\` se puede cerrar. Fue a favor (se evitó −1 R).
- 13-10: la cuenta empezó el 14-10.
- El resto: R real entre −0,11 y +0,07 frente a la réplica, media −0,022 R/op (spread y deslizamiento reales).

## Para la cuenta real
- Desde el 08-11 no ha operado (filtro p90). La última entrada fue el 06-11 a las 16:40. Con la v019, si el filtro
  sigue bloqueando, el día 21 es el 27-11 (Acción de Gracias, festivo, no opera) y **la primera operación forzada
  sería el lunes 30-11 al 25 % del riesgo**, antes del límite de 30 días de FTMO (06-12).
- La v019 del tope escribe `ORB_AGR_v018_live.csv` (sin nº de cuenta). Con una sola cuenta en el PC no pasa nada,
  y `estado_mt5.ps1` sigue leyendo el nombre de siempre.

## v020 propuesta
`/mnt/project-files/validacion-v019/ORB_US100_AGR_v020.mq5` = v019 del tope + nº de cuenta en el CSV live (una línea,
mismo cambio que la otra v019). Hace falta para las cuentas de Black Friday en el mismo PC. Pendiente: compilarla en
el laboratorio y actualizar `estado_mt5.ps1:41` antes de usarla.

## Ficheros
- `replica.py`: réplica de v018/v019 (tope opcional, stop de entrada a +2 R en fondeada).
- `paseo_orb.py`: prueba P1. `validar_v019.py`: P5 contra el tester sin simulador y contra la cuenta real.
- `comparar_mt5.py`, `comparar_real.py`, `forzadas.py`: comprobaciones intermedias con el tester con simulador.
- `datos/`: CSV del tester del laboratorio (C:\MT5_Lab, US100_FTMO M1 OHLC, 2022-01-03 → 2026-11-07), log de las
  operaciones forzadas y velas M1 de FTMO del 25-09 al 06-11-2026.
- Cambio en `metodo/comparar_ops.py`: el lado del CSV de MT5 se normaliza también («LONG»/«SHORT»). Antes, un
  DataFrame con el lado en texto que no pasaba por `cargar_mt5` no emparejaba nada. Hay un test nuevo para esto.
