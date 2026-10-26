# Preregistro: continuación del shock de 08:30 NY (2026-10-26, antes de mirar datos)

1. Regla: en la vela de 5 minutos 08:30-08:35 NY, si su rango es > 3 veces la mediana de los 60 días
   anteriores para ese mercado, entrar al cierre (08:35) en la dirección de esa vela. Stop = rango de
   la vela de shock. Salida: 10:00 NY o stop. Máximo 1 operación al día por mercado.
2. Mercados a la vez: XAUUSD, US500, US30, US2000 (Dukascopy M1 bid/ask) y EURUSD como quinto.
3. Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 abierto una sola vez.
4. Métrica: R bruta y neta (spread real + comisión 5 $/lote ida y vuelta) por operación;
   placebo = la misma regla con dirección aleatoria y las mismas salidas (200 réplicas).
5. Umbral: embudo.py estándar. n_pruebas = 10 (5 mercados × 2 lados contados como diagnóstico).
Hipótesis causal: los datos macro de 08:30 NY obligan a recolocar carteras; la difusión de la
información es gradual (reacción insuficiente), así que la primera dirección continúa hasta media sesión.
