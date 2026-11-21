# v16 — Preregistro de la confirmación (escrito el 20-11-2026 antes de abrir 2023-26)

## De dónde salen las hipótesis
Mapa de exploración 2018-22 (`fase2_mapa.py`): 4.628 pruebas (5 mercados elegidos al azar con
semilla 20261120 × velas cada 30 min × H 1 h/3 h × 13 condiciones). Nulo por permutación, 50
repeticiones: umbral FWER 5 % |t| ≥ 4,92; |t| ≥ 3 → real 52 frente a 27,7 de media en el nulo
(p95 37). Hay más estructura que azar, casi toda en EURUSD (36 de 52).

Regla de selección fijada antes de mirar fuera: |t exploración| ≥ 4 **y** efecto ≥ 2× coste.
Salen 4 (y ninguna más):

| id | mercado | entrada UTC | salida | condición (medida antes de entrar) | lado | t exp | efecto/coste |
|---|---|---|---|---|---|---|---|
| C1 | EURUSD | 01:30 | 02:30 | apertura 01:30 en el tercio bajo del rango de ayer | largo | +5,62 | 2,1 |
| C2 | EURUSD | 06:00 | 07:00 | día anterior en el tercio bajo (cayó) | corto | −4,47 | 2,9 |
| C3 | EURUSD | 09:00 | 12:00 | todos los días | corto | −4,02 | 2,9 |
| C4 | XAUUSD | 06:30 | 07:30 | día anterior en el tercio bajo (cayó) | largo | +4,31 | 3,0 |

Cortes de tercio: los de exploración, congelados (se guardan en `salidas/cortes_v16.json`).
Horas en UTC fijas (sin ajustar horario de verano: así se exploraron).

## Qué se mide fuera (2023-01-01 → 2026-10-23), una sola vez
Operación real con el motor (`motor.operar`): entrada en la apertura de la vela, salida al cierre
de la última vela, stop de emergencia 0,5·ATR14 revisado vela a vela con huecos. Coste = el de
`datos.COSTE` o media horquilla Dukascopy + 0,2 pb, el mayor.

Puertas para cada candidata (todas):
1. neto medio > 0 con t por semana ≥ 2,24 (Bonferroni una cola 5 %/4);
2. neto con costes ×2 > 0;
3. neto > 0 en 2023-24 y en 2025-26;
4. placebo de hora: la misma regla (misma condición, lado, H) en todas las demás velas líquidas
   de ese mercado fuera de muestra; la candidata debe superar el p95 de su t;
5. aviso (no bloquea): efecto fuera ≥ 50 % del de exploración.

Si pasa alguna, sigue al embudo P0 (coste en R ≤ 0,10, ≥ 40 ops/año, bruto ≥ 3× coste) y P4
(correlación con el ORB). Lo que no pase queda DESCARTADO; no se reajustan horas ni condiciones
con los datos de fuera.

## Coincidencias con descartes previos
- C3 (EUR cae en horario europeo) es la estacionalidad FX por horario de Breedon-Ranaldo (2013),
  que la búsqueda v3 tiró en T0 **sin datos**. Aquí sale de los datos sin buscarla.
- C4 se parece a «oro largo en Asia» (descartado 25-10, efecto ≈ coste) pero es otra hora
  (06:30 UTC, apertura europea) y condicionada a la caída de ayer.
