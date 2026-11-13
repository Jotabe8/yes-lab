# Preregistro: amplitud de apertura y movimiento "estrecho" del índice (13-11-2026)

Hipótesis: si en los primeros 5 minutos el índice sube (o baja) pero la mayoría de acciones va en
contra, el movimiento lo empujan pocas mega caps (flujo de futuros/ETF o una noticia de un solo valor)
y tiende a deshacerse durante la sesión. Si el movimiento es amplio, continúa. Información nueva: el
proyecto nunca ha usado las acciones componentes para operar el índice.

Regla (fija):
- Amplitud B = fracción de las 71 acciones grandes (mín. 50 con datos) con cierre 9:34 > apertura 9:30 (precio medio).
- m = movimiento del índice 9:30→9:35.
- ESTRECHO (principal): m > 0 y B < 0,40 → corto; m < 0 y B > 0,60 → largo. Entrada 9:35, salida 15:55 NY.
- AMPLIO (secundaria): m > 0 y B > 0,60 → largo; m < 0 y B < 0,40 → corto.
- Mercados: US100, US500, US30 (M1 bid/ask Dukascopy). Coste: horquilla real + 0.
- Métrica: pb por operación y R con R = 0,25 × ATR14 diario del índice.
Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 una vez. Placebo: dirección aleatoria en los mismos días.
Puertas del embudo; para ESTRECHO además corr diaria con el ORB US100 < 0,3.
