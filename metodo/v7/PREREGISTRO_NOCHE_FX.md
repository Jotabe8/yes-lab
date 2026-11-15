# Preregistro v7: scalper nocturno en cruces FX (fuente: historiales reales de terceros)

Fecha: 2026-11-14, escrito ANTES de descargar ningún dato de estos pares.

## Por qué esta fuente
Las búsquedas v1-v6 generaban candidatos desde ideas propias, minería o artículos. La fuente nueva son
cuentas reales de terceros con años en vivo. Revisión de MQL5 Signals ordenado por antigüedad (14-11-2026):
los supervivientes largos son casi todos (1) rejillas/promediado en cruces de rango (AUDCAD, NZDCAD, AUDNZD),
(2) EAs de oro y (3) "night scalpers" de sesión asiática. (2) ya está probado (ORB oro, Bollinger oro).
(1) y (3) comparten la misma señal de fondo (reversión en horas tranquilas); la rejilla solo cambia la forma
de la cola, no la esperanza, así que se prueba la señal sin promediar.
Ancla: "Night Hunter Pro All Pairs" (mql5.com/en/signals/856907): IC Markets live desde 27-10-2020, 314 semanas,
2.156 ops, 68 % ganadoras, PF 1,23, mantenimiento medio 11 h, pares GBPUSD EURCAD EURUSD CHFJPY AUDCAD EURAUD
EURCHF USDCAD USDCHF. Coste IC Markets raw (≈0,1-1 pip + 7 $/lote) es parecido al de FTMO (5 $/lote).
En el registro de ideas no hay ninguna prueba de reversión nocturna en cruces (solo majors y oro en horario general).

## Regla (única, fijada aquí)
- Datos: Dukascopy M15 bid y ask, 2010-01-01 → 2026-11-01. Hora convertida a America/New_York.
- Pares de decisión (los 9 del ancla): GBPUSD EURCAD EURUSD CHFJPY AUDCAD EURAUD EURCHF USDCAD USDCHF.
- Pares de réplica (no mirados hasta el final): AUDNZD NZDCAD GBPCHF EURNZD.
- Indicadores sobre el precio medio (bid+ask)/2, M15: SMA20, desviación típica 20, ATR14.
- Entrada: barra que CIERRA entre 18:30 y 23:00 NY con cierre medio > SMA20 + 2σ → corto; < SMA20 − 2σ → largo.
  Se entra a la apertura de la barra siguiente (corto al bid, largo al ask). Una operación por par y noche.
- Stop: 3 × ATR14 desde el precio de entrada; R = esa distancia. Se mira barra a barra con el lado real
  (largo: bid bajo; corto: ask alto); si la barra abre más allá del stop, sale a la apertura.
- Salida: primer cierre medio que cruza la SMA20 → sale a la apertura siguiente; o salida por tiempo a la
  apertura de la barra de las 02:00 NY. Nunca cruza el cambio de día de las 17:00 NY (sin swap).
- Coste: horquilla real de Dukascopy (entrada y salida en el lado real) + comisión 5 $/lote ida y vuelta
  (0,005 % del nominal). Bruto = mismo cálculo en precio medio sin comisión.

## Variantes informativas (máx. 2, no deciden)
V2: bandas 2,5σ. V3: ventana de entrada hasta 01:00 NY.

## Criterios (todos)
1. Cartera de decisión (9 pares, 1 R cada op): R neta media con t ≥ 2,4 en 2010-26.
2. 2010-17 > 0 y 2018-26 > 0 con t ≥ 1,5 cada mitad; 2023-26 > 0.
3. Con coste ×2 la R media sigue > 0.
4. Placebo de hora: la misma regla con entradas 08:00-12:00 NY tiene que ser peor (si es igual, no es la noche).
5. Placebo de dirección: 200 carteras con lado aleatorio y las mismas salidas; la real > p95.
6. Réplica en los 4 pares no mirados: R neta media > 0 con t ≥ 1,5.
7. Correlación diaria con la serie v018 < 0,3.
8. Peor racha (DD en R a 1 R por op, cartera) < 3 × beneficio medio anual en R.
Si pasa: medir horquilla FTMO real de noche en MT5 antes de cualquier EA (Dukascopy no es FTMO).
Si no pasa: se descarta la familia "reversión nocturna FX" y su versión en rejilla, sin reserva.
