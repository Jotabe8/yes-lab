# Preregistro: ciclo de la Fed, semanas pares (2026-10-26, antes de mirar datos)

1. Regla: contar sesiones desde cada anuncio del FOMC (día 0). Semana k = floor((sesiones + 1) / 5),
   así la semana 0 va del día −1 al +3. Comprar el índice al cierre anterior al inicio de una semana
   par (0, 2, 4, 6) y vender al cierre de su último día. Stop = 2 × ATR(20) D1, comprobado cada día
   con el mínimo; si abre por debajo, se llena a la apertura. Sin objetivo.
2. Mercados a la vez: US500, US30, US100, US2000, GER40, FRA40, EU50, UK100, JP225, HK50, AUS200 (D1 Dukascopy).
3. Periodo: ajuste 2011-2018; fuera de muestra 2019-2025 abierto una sola vez (el artículo usa 1994-2016).
4. Métrica: R bruta y neta (spread típico FTMO + financiación 0,02 % por noche natural);
   placebo = misma regla con el ciclo desplazado un número aleatorio de sesiones (200 réplicas);
   control = estar comprado en semanas impares (debe salir peor).
5. Umbral: embudo.py estándar. n_pruebas = 11 (mercados).
Hipótesis causal (Cieslak, Morse y Vissing-Jorgensen 2019): la Fed comunica de forma informal en
semanas pares (reuniones del consejo, discursos) y la prima de las acciones se concentra ahí.
