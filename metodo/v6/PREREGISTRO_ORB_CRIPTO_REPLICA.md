# Preregistro: réplica del ORB de NY en criptomonedas no miradas (14-11-2026)

Escrito antes de descargar ningún dato de estas monedas. Jorge pide un 2º sistema que diversifique el ORB US100.

## Por qué
La única pista viva es el ORB de ETH a las 9:30 NY (+0,15 R neto en 2024-26 si el coste total es ≤ 0,04 %).
Dos problemas ya vistos en `metodo/v3/cripto_medio_salida.txt`:
1. El lado contrario (placebo) también gana: ETH +0,178 R (t 2,46) frente a +0,253 del lado de la vela;
   el exceso es +0,037 (t 0,67). La elección del lado apenas aporta: lo que gana es la forma del pago
   (stop corto y aguantar hasta las 15:55 en la sesión de EE. UU.).
2. ETH y BTC salieron de mirar 2 monedas × 5 rangos: hace falta una réplica no mirada.

Dos hipótesis, cada una con su placebo:
- **H1 (dirección, la del ORB):** el lado de la vela del rango gana más que el lado contrario.
- **H2 (sesión):** la llegada del flujo de EE. UU. a las 9:30 crea tendencia intradía; la media de ambos lados a
  las 9:30 supera a la misma operación a la 01:00 NY (hora sin flujo de EE. UU.).

## Datos
Perpetuos USDT-M de Binance, velas M1 de data.binance.vision, 2021-03-01 → 2026-10-31 (precio negociado).
Monedas fijadas de antemano (las 8 más líquidas listadas antes de 2021, sin BTC ni ETH):
SOL, XRP, BNB, DOGE, ADA, LINK, LTC, AVAX. ETH y BTC de Binance solo como comprobación de fuente (no cuentan).

## Regla (idéntica a la v3, rango 10 min)
Rango 9:30-9:40 NY, lado de la vela del rango (cuerpo ≥ 10 % del rango), entrada a la apertura de las 9:40,
stop 0,15 × ATR14 de la sesión 9:30-16:00, stop vela a vela, salida 15:55. Solo días laborables.
Placebo H1: el mismo momento con el lado contrario. Placebo H2: la misma operación empezando a la 01:00 NY.

## Coste
Sitio objetivo: Lighter cuenta estándar (0 % comisión). Coste supuesto 0,03 % ida y vuelta (horquilla,
deslizamiento por los 300 ms de latencia y ~0,008 % de financiación). Sensibilidad ×2 (0,06 %).

## Criterios (cartera de las 8 monedas a partes iguales por día)
Pasa si se cumplen todos:
1. Neto 2021-03 → 2026-10 con t ≥ 2,4.
2. Neto > 0 en 2024-26 y en cada mitad del periodo.
3. Costes ×2 > 0.
4. H1: exceso sobre el lado contrario con t ≥ 2,0, **o** H2: (media de ambos lados 9:30) − (01:00) con t ≥ 2,0.
5. Al menos 5 de las 8 monedas con neto > 0.
6. Correlación diaria con la serie v018 < 0,3.
Dos hipótesis → listón de t de los placebos ya corregido (2,0 ≈ p 0,025 unilateral por hipótesis, Bonferroni 5 %).

Si pasa: el ORB de ETH (y la cartera cripto) se opera en Lighter con un bot de Python y capital propio.
Si no pasa: el ORB cripto se descarta del todo y el disparador de ETH se cierra.
