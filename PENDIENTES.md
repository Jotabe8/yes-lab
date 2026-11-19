# Pendientes: vigilancia del ORB US100 en real

Actualizado el 19-11-2026. Contexto: `metodo/vigilancia.py` (cruce diario real vs réplica + SPRT de Wald).

## Abiertos

| # | Tarea | Quién | Bloqueo |
|---|---|---|---|
| 1 | Para el detalle de las 6 primeras ops: localizar el CSV de operaciones del EA en el PC (buscar en `%APPDATA%\MetaQuotes` con `-Force`, o en MT5: Archivo → Abrir carpeta de datos → MQL5\Files) y mandarlo por correo como adjunto | Jorge | `ops_live.csv` no aparece en C:\ sin `-Force` |
| 2 | Réplica del Strategy Tester (ticks reales FTMO, parámetros del EA) de los mismos días del reto, con columnas `fecha, lado, R` | Jorge | Necesita el PC |
| 3 | Pasar las 14 ops una a una por `python -m metodo.vigilancia real.csv replica.csv` (SPRT y cruce día a día) | Claude | Depende de 1 y 2 |
| 4 | Plan de escalado entre firmas (FTMO, tope 400.000 $; ya están preparadas las instalaciones MT5_FTMO_10K_A y B) | Claude | Aparcado |

## Cerrados

- **PR de la vigilancia** (Jotabe8/yes-lab#54): fusionada el 19-11.
- **Operaciones desde los correos**: los informes diarios dan el detalle de las 8 ops del 26-10 al 6-11; las 6 anteriores (14 al 23-10, antes de que empezaran los informes) solo como suma, +0,76 R. Cuadra con el acumulado (14 ops, +2,24 R). No hay correos automáticos de MT5.

- **Rutina del informe diario con el SPRT**: desde el 18-11 el informe muestra "SPRT: 14 operaciones, suma +2,24 R, margen hasta la parada 43,5 R → seguir".
- **Suelo de pérdida máxima tras el reinicio del 13-11**: corregido; vuelve a ser 9.376,10 $ (informe del 18-11).

## Estado a 19-11-2026

ORB_US100_AGR_v019 en la 1-Step 10K (531498006). 14 operaciones en el reto, +2,24 R; SPRT **seguir** (parar si
suma ≤ −41,2 R). Sin operaciones desde el 6-11: el filtro de volatilidad bloquea (percentil 99-100); a los 21 días
sin operar el EA abre una operación forzada al 25 % del riesgo.
