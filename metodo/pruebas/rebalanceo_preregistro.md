# Preregistro: rebalanceo 60/40 de fin de mes (2026-10-26, antes de mirar datos)

- **Hipótesis (Harvey, Mazzoleni y Melone, NBER 33554):** si en el mes las acciones baten a los bonos, los fondos 60/40 venden acciones en los últimos días del mes y el índice cae; si ganan los bonos, compran y sube.
- **Regla:** al cierre de la 6.ª sesión antes del fin de mes, señal = rentabilidad del mes de US500 − rentabilidad del mes de IEF (bonos 7-10 años). Señal > 0 → corto; < 0 → largo. Salida al cierre de la última sesión del mes (5 sesiones). Stop de catástrofe 1,5 ATR(20) D1; R = resultado / (1,5 ATR).
- **Mercados (P1, a la vez):** US500, US100, US30, US2000 (mismo flujo en EE. UU.) y GER40, UK100, EU50 (control: el flujo de fondos de EE. UU. debería pesar menos).
- **Datos:** D1 Dukascopy del PC (data/D1), IEF ajustado de yes-lab. Muestra 2016-11 a 2025-12 (fin de los D1). Ajuste hasta 2022, prueba 2023-2025 abierta una vez.
- **Coste:** 0,05 R por operación (spread + 5 noches de financiación).
- **Variantes contadas (n_pruebas):** 7 mercados × 2 (todas las señales / solo |señal| > 2 %) = 14.
- **Pasa P1 si:** bruto ≥ 3× coste en US500 y en al menos 3 de los 4 índices de EE. UU., y supera el p95 de un placebo de dirección aleatoria en los mismos días.
- **Aviso de P0:** 12 operaciones/año por índice, por debajo del mínimo de 40. Solo serviría como complemento del ORB en la misma cuenta; se sigue a P1 porque probarlo cuesta minutos.
