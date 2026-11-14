# Preregistro: zona de ruido (Zarattini, Aziz, Barbon 2024) en GER40 y UK100. 2026-11-14, antes de descargar datos

Fuente: "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", SFI 24-97 (SPY 2007-24, Sharpe 1,33 neto).
Réplicas de 2026: Chuk (SSRN 7609644, futuros NQ) y Paz (SSRN 7290621, SPY fuera de muestra). En US100 ya se probó (clase D, correlada con el ORB).
Aquí es nueva: índices europeos, que no se solapan con el ORB US100 (corr ORB GER40/US100 = 0,00). Lo pidió Jorge el 14-11.

## Reglas (fijas)
- Datos: Dukascopy M1 bid/ask → precio medio, hora local. GER40 y EU50: 9:00-17:30 Fráncfort. UK100: 8:00-16:30 Londres. 2013-01 → 2026-11.
- Para cada minuto k desde la apertura: σ_k = media en las 14 sesiones anteriores de |cierre_k / apertura − 1|.
  Banda superior = max(apertura, cierre de ayer)·(1+σ_k); inferior = min(apertura, cierre de ayer)·(1−σ_k).
- Decisión cada 30 min desde la apertura + 30 (9:30, 10:00…; Londres 8:30…), con el precio de ese instante.
  Largo si precio > max(banda sup, VWAP); corto si < min(banda inf, VWAP). Stop dinámico: un largo sale si precio ≤ max(banda sup, VWAP), un corto si ≥ min(banda inf, VWAP); puede girar.
  VWAP con el volumen de ticks de Dukascopy (si no hay, precio medio sin ponderar). Cierre forzado a las 17:25 / 16:25.
- Unidad: rentabilidad del día con exposición 1×, dividida por la desviación de la rentabilidad apertura-cierre de las 14 sesiones anteriores ("R" del día; equivale al dimensionado por volatilidad del paper).
- Coste por operación (ida y vuelta) = horquilla FTMO medida: GER40 0,0052 %, UK100 0,0079 %, EU50 0,0268 %.
- Variantes (3): base; contraria (desvanecer la ruptura, sale al volver dentro de la banda) = placebo de lado; desfase de 15 min en las decisiones = placebo de hora/robustez.

## Listón (v3, toda la historia)
- Cartera GER40 + UK100 (media de los R diarios): neto t ≥ 2,4 en 2013-26; las dos mitades > 0; costes ×2 > 0.
- Cada mercado con bruto > 0. La contraria debe dar < 0. Desfase 15 min > 0 (si la ventaja depende del minuto exacto, es ruido).
- Placebo: 500 permutaciones del signo de cada operación (mismos tiempos) → la real por encima del p95.
- EU50 = réplica no usada para decidir: bruto > 0.
- Corr diaria con ORB v018 < 0,3. DD a vol 15 % < 3 × rentabilidad anual. ≥ 40 ops/año.
