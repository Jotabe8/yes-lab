# Preregistro: reversión del hueco nocturno entre índices (CO-OC), 2026-10-26, antes de mirar datos

1. Regla: cada día, en la apertura de la sesión, ordenar los índices del grupo por su rentabilidad
   nocturna (cierre anterior → apertura). Comprar el que menos ha subido y vender el que más, mismo
   nocional, y cerrar ambos al final de la sesión. Sin stop (posición neutral e intradía).
2. Mercados: dos grupos independientes. EE. UU.: US500, US30, US2000 (09:30-16:00 NY).
   Europa: FRA40, EU50, UK100 (apertura 09:00 CET, cierre 21:55 CET, sesión CFD).
3. Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 abierto una vez.
4. Métrica: rentabilidad bruta y neta (spread real Dukascopy en las cuatro patas) en % y en R,
   con 1 R = desviación típica diaria de la estrategia en ajuste. Placebo = lados al azar (200 réplicas).
5. Umbral: embudo.py estándar en cada grupo; tiene que funcionar en los dos. n_pruebas = 2.
Hipótesis (QuantReturns 2025, "Overnight Mean-Reversion"): la noche concentra los flujos de un solo
índice (resultados, noticias locales) y la sesión siguiente devuelve parte de la divergencia.
