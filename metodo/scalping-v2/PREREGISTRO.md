# Preregistro: scalping con edge, familias nuevas (14-11-2026, antes de ver datos)

Pedido de Jorge: "Busca una estrategia de scalping con edge". Ya descartado y NO se repite: scalping NNFX M1/M5/M15
(0/105), scalping de coste bajo (EMA20 GER40 M30 cayó), reversión intradía, VWAP, breakout/fade de noticias US100,
shock 08:30, periodicidad, zona de ruido, scalper nocturno FX/rejillas (v7).

## Datos
- M1 bid + spread real por minuto (hora servidor = NY+7): US100 (Dukascopy 2018-22 + FTMO 2023-26), GER40 FTMO
  (2021-26), US30 y US500 Dukascopy 2018-26.
- Ticks bid/ask FTMO de GER40 (22-11-2021 a 08-05-2026). No hay ticks de US100 en el PC.
- Desequilibrio del libro: NO es comprobable. Un CFD no tiene libro; los ticks FTMO solo traen bid/ask (sin
  profundidad ni volumen real). Se deja fuera y se dice.

## Reglas comunes
- Largos entran al ask y salen al bid; cortos al revés (spread real del minuto o del tick). Sin swap: todo intradía.
- Stop recorrido minuto a minuto; si en el mismo minuto tocan stop y objetivo, cuenta el stop.
- Se salta una señal si spread / riesgo > 0,10 R (filtro P0 de coste).
- Ajuste 2018-22, prueba 2023-26 (abierta una sola vez). GER40: ajuste 2021-23, prueba 2024-26.
- PASA solo si: neto > 0 en ajuste y prueba; t ≥ 2,4 en prueba; neto > 0 con coste ×2; por encima del p95 del
  placebo (20 repeticiones, mismas entradas y salidas, dirección aleatoria); mismo signo bruto en ≥ 2 de los otros
  3 índices; bruto por operación ≥ 3 × coste ida y vuelta; ≥ 40 ops/año.
- Paseo aleatorio: el mismo código sobre precios con los rendimientos M1 barajados dentro de cada día debe dar ≈ 0.
- Historia larga (US100 2011-17) solo si algo llega a pasar la prueba.

## F1. Barrido de liquidez (stop run) y vuelta (6 variantes)
- Niveles: (a) máximo/mínimo de la sesión de contado anterior; (b) máximo/mínimo de la pre-apertura del día.
- Ventana: primeros 120 min de contado (US 16:30-18:30 servidor; GER40 10:00-12:00).
- Evento: una vela supera el nivel y, en ≤ 5 velas desde la primera rotura, una vela CIERRA de vuelta dentro.
  Entrada contraria a la apertura del minuto siguiente. Stop = extremo del barrido + 1 spread.
- Salidas: (i) objetivo 1 R, (ii) objetivo 2 R, (iii) salida por tiempo a 30 min. Una operación por nivel y día.

## F2. Microestructura de la apertura: desvanecer el primer impulso (6 variantes)
- M1 (4 índices): ventana W = primer minuto o primeros 5 min de contado. Si la ventana sube, corto a la apertura
  del minuto siguiente (y al revés). Stop = extremo de la ventana + 1 spread. Salida a 5 o 15 min. (4 variantes)
- Ticks GER40: ventana = primeros 30 s desde las 09:00:00 de Fráncfort; entrada al primer tick tras 30 s con su
  bid/ask; stop = extremo de los 30 s + spread; salida a 2 o 5 min. (2 variantes)
- La continuación de la apertura es el ORB (ya en vivo); aquí solo se prueba el desvanecimiento.

## F3. Números redondos intradía en índices (2 variantes)
- Niveles: múltiplos de 100 (US100, US30, GER40) y de 25 (US500). Primer toque del nivel en la sesión de contado,
  llegando desde ≥ 0,2 ATR diario de distancia (desde la apertura de la sesión). Entrada contraria al tocar.
- Stop = 0,1 ATR(20) diario; objetivo 1 R o 2 R; salida máxima a 60 min o fin de sesión.
- Placebo propio: niveles desplazados un 37 % del paso (no redondos), mismas reglas. Debe ganar al desplazado.

Total: 14 variantes. Nada se añade después de ver resultados.
