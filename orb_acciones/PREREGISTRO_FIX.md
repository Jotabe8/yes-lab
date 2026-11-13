# Preregistro: reversión tras el fix de Londres (WM/R 16:00) en forex

Mecanismo: gestores y bancos ejecutan órdenes al precio del fix WM/R (ventana 15:58-16:02 Londres). Los bancos se cubren antes (precio empujado en la dirección del flujo entre 15:30 y 16:00) y el precio devuelve parte después (Melvin y Prins 2015; Evans 2018; Krohn et al. 2024). Intradía, sin swap.

Regla: señal = rendimiento medio 15:30→16:00 Londres. Entrada a las 16:05 en contra (largo si cayó, corto si subió), salida a las 16:30 (V1) o 17:00 (V2). Solo días con |señal| sobre la mediana móvil de 60 días (V3 = V2 filtrada). Entra a ask/bid de Dukascopy (spread real incluido) + comisión FTMO 0,35 pb ida y vuelta.
Mercados: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD. Datos M1 bid/ask Dukascopy 2012-2026.
Pruebas: 3 variantes en la cesta de 6 pares = 3 pruebas principales (+ desglose por par informativo).
Ajuste 2012-2022, OOS 2023-2026 abierto una vez.
Listón flexible: cesta neta > 0 con t ≥ 2 en ajuste, OOS neto > 0, supera placebo (misma regla con ventana 11:30→12:00 / 12:05→12:30-13:00), ≥ 4/6 pares positivos brutos.
