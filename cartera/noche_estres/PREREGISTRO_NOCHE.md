# Preregistro: prima nocturna tras un día de estrés (2026-10-26, antes de mirar datos)

1. Regla: si la sesión americana (09:30-16:00 NY) cierra con una caída mayor del 1,5 %, comprar
   el índice al cierre de las 16:00 y cerrar a las 09:35 NY del día siguiente. Stop = 1 % del precio.
2. Mercados a la vez: US500, US30, US2000 (Dukascopy M1 bid/ask).
3. Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 abierto una sola vez.
4. Métrica: R bruta y neta (spread real de entrada y salida, índices sin comisión en FTMO);
   placebo = comprar la noche de días elegidos al azar con la misma salida (200 réplicas).
5. Umbral: embudo.py estándar. n_pruebas = 6 (3 mercados × el umbral de caída como diagnóstico).
Hipótesis causal: la prima por mantener riesgo de un día para otro se concentra cuando la
aversión al riesgo acaba de subir; quien tiene que reducir riesgo vende en el cierre.
