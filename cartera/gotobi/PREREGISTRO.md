# Preregistro: efecto Gotobi en USDJPY (2026-10-26, antes de mirar datos)

1. Regla: los días gotobi (5, 10, 15, 20, 25 y último del mes; si cae en fin de semana o 1-3 de enero, el día hábil anterior) comprar USDJPY a las 08:00 JST y cerrar a las 09:55 JST (fijación de Tokio). Stop = 0,25 × rango diario medio de 14 días. Sin objetivo.
2. Mercados: USDJPY, EURJPY y GBPJPY (cruces sintéticos con EURUSD/GBPUSD de Dukascopy); EURUSD como control negativo (debe salir ~0).
3. Periodo: ajuste 2018-2022, fuera de muestra 2023-2026 abierto una vez.
4. Métrica: R bruta y neta (spread real de Dukascopy + comisión FTMO 5 $/lote ida y vuelta) por operación; placebo = mismos horarios en días hábiles aleatorios no gotobi (200 réplicas).
5. Umbral: embudo.py estándar (bruto ≥ 3× coste, > p95 placebo, neto ×2 > 0, ≥ 60 % años +, OOS t ≥ 1, EV recortada > control). n_pruebas = 4 (3 mercados + la ventana diaria como diagnóstico).
Hipótesis causal: importadores japoneses compran dólares en la fijación de los días de liquidación (gotobi); flujo obligado, documentado por Ito y Yamada (2017) y Bessho et al.
