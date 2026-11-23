# v20 — VWAP como base de una estrategia (preregistro, 23-11-2026)

Escrito antes de bajar el volumen y de mirar ningún resultado. Pedido de Jorge: "estudia el uso de VWAP para hacer
una estrategia con ventaja".

## Qué se probó ya (no se repite tal cual)
- VWAP reversión US100 (24-10, sin bruto) y "VWAP, the Holy Grail" de Zarattini y Aziz 2023 en QQQ (sin bruto).
- Zona de ruido + VWAP como stop dinámico (v8, se apaga). Toda la familia "dirección con el propio precio" 0/28.

Lo nuevo aquí: (1) volumen real (ETF por Alpaca, SIP) frente al volumen de Dukascopy y frente a no ponderar (TWAP),
para saber si el VWAP aporta algo que no tenga una media del precio; (2) cuatro mercados a la vez con costes FTMO;
(3) dos usos que no se habían probado: el desequilibrio del cierre frente al VWAP como señal del día siguiente y el
VWAP como salida del ORB.

## Mecanismo (y por qué el listón previo es bajo)
Los algoritmos de ejecución VWAP reparten la orden según el perfil de volumen esperado, no según el precio: no crean
un flujo que dependa de dónde está el precio respecto al VWAP. El único mecanismo plausible es indirecto: un cierre muy
por encima (debajo) del VWAP indica que la presión compradora (vendedora) se concentró al final, y las metaórdenes
institucionales que se reparten en varios días siguen al día siguiente (H1). Lo demás (bandas, cruces) es folclore
que se prueba una vez con volumen real para cerrar la familia.

## Datos y reglas comunes
- Mercados: US100, US500, US30 (sesión 9:30-16:00 NY) y GER40 (9:00-17:30 Berlín). M1 precio medio Dukascopy
  (matrices de v15) + volumen M1 de Dukascopy (lado bid, `dukascopy-node -v`). Para los US, volumen real de QQQ,
  SPY y DIA (Alpaca SIP, barras de 1 min, 2016-2026) aplicado como peso sobre el precio del CFD minuto a minuto.
- VWAP de sesión anclado a la apertura: sum(v·p)/sum(v), p = (H+L+C)/3 del minuto. σ = desviación típica
  ponderada por volumen de p alrededor del VWAP desde la apertura.
- Decisión con el volumen de Dukascopy (el más parecido a lo que ve un EA, volumen de ticks). Las otras dos
  ponderaciones solo como comparación.
- Exploración P1: 2012-01-01 a 2022-12-31. Fuera de muestra P3: 2023-01-01 a 2026-11-13, se abre una vez y solo
  para lo que pase P1.
- Coste de ida y vuelta (fracción del precio): horquilla FTMO de apertura + 0,2 pb de deslizamiento:
  US100 0,69e-4, GER40 0,72e-4, US500 0,80e-4, US30 0,80e-4. En las operaciones de muchas entradas el coste se
  cobra en cada ida y vuelta.
- ATR14 de sesión del día anterior (solo información pasada).

## D0 (diagnóstico, no decide): ¿VWAP ≈ TWAP?
Correlación de (P − VWAP)/ATR a las 10:30, 12:00, 14:00 y 15:55 entre las tres ponderaciones, y % de minutos en que
el signo de P − VWAP coincide. Si coincide > 95 %, las reglas de VWAP son reglas de media del precio y el tipo de
volumen (real o de ticks) no cambia nada.

## H1 — Desequilibrio del cierre frente al VWAP → mismo lado al día siguiente (intradía, vale para FTMO)
- z_d = (C_d − VWAP_d)/ATR, con C_d el cierre de sesión.
- Umbral: cuantiles 80 % y 20 % de z en los 250 días anteriores (sin mirar el futuro).
- z > q80 → largo el día d+1; z < q20 → corto. Entrada en la apertura de la sesión + 1 min, stop 0,5·ATR
  (comprobado vela a vela, hueco al precio de apertura de la vela), salida 5 min antes del cierre. 1 R = 0,5·ATR.
- Control: el mismo con la señal del rendimiento del día d (C_d − O_d) en vez de z; H1 debe ganar al control
  (regresión r_{d+1} ~ z + rend_d: el coeficiente de z con t ≥ 2).
- Placebo: mismos días y salidas con dirección al azar (1.000 réplicas).

## H2 — VWAP como stop dinámico del ORB US100 (filtro/variante)
- Base: ORB de `metodo/rapido.py` (rango 9:30-9:40, vela del rango, stop 0,15·ATR, salida 15:55), sin el filtro de
  volatilidad p90 (los mismos días en las dos versiones).
- Variante: a partir de las 10:00, el stop pasa a ser max(stop inicial, VWAP) en largos y min(stop inicial, VWAP) en
  cortos, comprobado al cierre de cada M1; salida a la apertura de la M1 siguiente.
- Pasa si ΔR/op pareado > 0 con t ≥ 2 en US100 2012-22, el Sharpe anual sube, y el signo de Δ se repite en US500 y
  US30 (mismo ORB).

## H3 — Bandas VWAP ±2σ: vuelta al VWAP (reversión)
- De 10:30 a 15:00: si una M1 cierra > VWAP + 2σ → corto en la apertura de la siguiente; < VWAP − 2σ → largo.
- Objetivo: tocar el VWAP (del minuto). Stop: VWAP ± 3σ fijado en la entrada. Salida forzada 15:55. Una operación
  por lado y día. 1 R = distancia al stop.
- Placebo: mismas entradas y salidas con dirección al azar.

## H4 — Tendencia VWAP (Zarattini y Aziz 2023) en 4 mercados con coste
- Siempre dentro de 9:31 a 15:55: largo si la vela cierra por encima del VWAP, corto si por debajo; se gira en cada
  cruce. Dos marcos: M1 (como el artículo) y M5. Plano al cierre.
- Medida: rendimiento diario neto (fracción) y t; placebo: mismo número de giros en minutos al azar.

## Criterio P1 (por hipótesis; cuatro hipótesis, 4 mercados → la corrección se da como aviso)
- Neto medio por operación > 0 con t ≥ 2,5 juntando los mercados, ≥ 3 de 4 mercados con neto > 0, por encima del
  p95 del placebo y efecto bruto ≥ 3× coste. H2: su criterio propio.
- Lo que pase P1 sigue el embudo: costes ×2, meseta (umbrales 70/30 y 90/10 en H1), OOS 2023-26, corr con el ORB
  v018 < 0,3, EV de cuota. Lo que no pase se descarta (regla de Jorge: nada queda en reserva).
