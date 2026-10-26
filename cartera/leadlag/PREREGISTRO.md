# Preregistro: Asia marca el día en Europa (2026-10-26, antes de mirar datos)

1. Regla: a la apertura europea (09:00 CET) entrar en el índice europeo en la dirección del
   movimiento de la sesión asiática (JP225 + HK50, media de su variación 00:00-07:00 CET).
   Solo si esa señal supera 0,3 % en valor absoluto. Stop = rango de la sesión asiática del
   propio índice europeo (00:00-09:00 CET). Salida a las 12:00 CET o stop.
2. Mercados a la vez: GER40, FRA40, EU50, UK100 (Dukascopy M1 bid/ask).
3. Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 abierto una sola vez.
4. Métrica: R bruta y neta (spread real, índices sin comisión en FTMO); placebo = misma regla
   con la dirección aleatoria y las mismas salidas (200 réplicas).
5. Umbral: embudo.py estándar. n_pruebas = 8 (4 mercados × el umbral de señal como diagnóstico).
Hipótesis causal: la información de la sesión asiática se incorpora despacio en Europa
(difusión gradual entre husos horarios), y la apertura europea no recoge todo el movimiento.
