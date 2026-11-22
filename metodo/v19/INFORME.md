# v19 · Tendencia semanal en una cesta cripto — informe (22-11-2026)

Preregistro: `PREREGISTRO.md`. Código: `tendencia_cripto.py` (embudo P0-P4) y `diagnostico.py` (paseo, exceso sobre la
beta, P4 a mercado diario). Salidas: `salida.txt`, `diagnostico_salida.txt`. n_pruebas = 15 (7 en el libro de pruebas
+ log, BTC+ETH y 4 niveles de riesgo en P4; t_requerido 2,71).

**Regla:** cada domingo al cierre (00:00 UTC), comprado 7 días cada moneda cuyo rendimiento de 28 días es > 0, si no
fuera; tamaño 1/σ semanal (1 R = 1 σ). 20 monedas grandes de Binance contado, 2019-2026; ajuste hasta 2022, fuera
2023-01 → 2026-10.

## Veredicto

**Pasa P0-P4 en FTMO y en exchange según lo preregistrado, falla P4 en Darwinex Zero, y lleva tres banderas rojas
que no estaban en el preregistro.** No es un edge del tamaño del ORB: la mitad del resultado es la deriva alcista de
cripto 2019-26, y la parte que es cronometraje puro se ha debilitado desde 2023 y es negativa en 2025-26.

| Puerta | Resultado | |
|---|---|---|
| P0 coste | 0,006 R/op (exchange), 0,045 (DZ con swap 20 %), 0,054 (FTMO con swap 25 %); 464 ops/año | OK |
| P1 placebo (mismo tiempo dentro, momento al azar, 200) | bruto +0,220 R vs p95 +0,162; réplica 126 monedas +0,162 vs p95 +0,080 | OK |
| P1 paseo aleatorio | +0,091 R t 15,7 → **no es el motor**: es Jensen (E[eˣ−1] > 0 con media log 0); siempre comprado da +0,096 en las mismas velas y el exceso de la señal en el paseo tiene t medio −0,23 | OK tras explicarlo |
| P1 `sin_fuga` | sin fuga | OK |
| P2 costes ×2, años, meseta | ×2 +0,208 (exchange), +0,112 (FTMO); 6/8 años; lookback 22 d +0,192, 34 d +0,216 | OK |
| P3 fuera 2023-26 | exchange +0,172 t 1,82; DZ +0,126 t 1,33; FTMO +0,116 t 1,23 | OK |
| P3 t total (por semana) | exchange 3,19; DZ 2,60; FTMO 2,48 vs 2,71 | aviso en DZ/FTMO |
| P4 FTMO 2-Step 100K (R diaria a mercado, 0,2 %/moneda) | EV/cuota +6.274 € vs siempre comprado +3.471 € vs control media 0 +1.413 €; sin deriva de cripto +3.621 € | OK |
| P4 Darwinex Zero | Sharpe mensual ORB + reversión 1,92 → 1,96 con igual riesgo (umbral +0,10); 2023+ baja 2,05 → 1,87 | **NO** |
| Correlación mensual | ORB US100 −0,07; reversión DZ +0,11 | OK |

Swap de equilibrio (neto = 0): ~107 %/año. El swap de cripto no lo mata (supuesto DZ 20 %, FTMO 25 %, ambos sin verificar):
con σ semanal de 10-20 %, el nocional por R es pequeño.

## Banderas rojas (red team)

1. **Exceso sobre la beta** (Σ (señal − fracción media dentro) · R por semana, neutral a la exposición): t 2,26 total,
   ajuste 2,45, **fuera 0,97**. En log: t 1,89. Réplica: t 2,35, fuera 1,07. BTC+ETH solos: t 3,60, fuera 1,90.
2. **Se apaga**: bruto por año 2019 +0,09, 2020 +0,31, 2021 +0,54, 2022 −0,16, 2023 +0,26, 2024 +0,33, **2025 +0,08,
   2026 −0,03**. Exceso sobre la beta en 2026: −0,55 R/semana (réplica −2,84). Mismo patrón que el carry cripto (v4):
   publicado, popular y agotándose.
3. **Depende de la deriva**: siempre comprado con el mismo tamaño da Sharpe diario 0,58 (estrategia 1,00). Quitando la
   beta de su exposición media, Sharpe 0,54 en total y **0,27 desde 2023**, con 2025 −27 R y 2026 −72 R.
4. Supervivencia en el universo principal (monedas grandes hoy). La réplica (otro universo) mantiene el exceso, así que
   no es todo supervivencia, pero infla la beta.
5. Riesgo de un día: peor día −27 R con ~10 monedas a la vez (correlación alta entre monedas). Con 0,2 %/moneda es
   −5,4 %: rompería la pérdida diaria de FTMO ese día; el simulador lo cuenta, pero solo al cierre diario.

## Qué significa para cada sitio

- **FTMO (Swing)**: es el único sitio donde pasa, a 0,1-0,3 % por moneda (no al 1 %: 10-20 posiciones a la vez). Falta
  verificar en MT5 FTMO qué criptos hay, su swap real, horquilla y apalancamiento.
- **Darwinex Zero**: no suma al DARWIN de ORB + reversión (+0,04 de Sharpe, y resta desde 2023). Descartado para DZ.
- **Exchange sin swap**: pasa, pero no es una prop: sería capital propio y lo mismo que comprar cripto con un stop de
  tendencia.

## Siguiente paso si se sigue

P5: EA MQL5 multisímbolo (rebalanceo dominical, tamaño 1/σ, tope de exposición total) con los símbolos reales de FTMO,
comparación operación a operación y P6 en Free Trial/demo 8 semanas con parada si el exceso sobre la beta es < 0.

## P5 (22-11-2026): EA en el Strategy Tester con los símbolos reales de FTMO

Datos leídos de la cuenta FTMO (solo lectura, API de Python; nada cargado en ese terminal). Tester en C:\MT5_Lab con
símbolos personalizados `<SIM>_FTMO` (contrato, swap, margen y horquilla reales), 2017-01 → 2026-11, 100.000 USD, 0,2 %.

- **FTMO cripto**: 30 símbolos, swap **−30 %/año largo y corto** (modo interés anual, triple el viernes), margen 30 %
  (1:3,3), sin comisión, cotizan el fin de semana. No existen TRX, ATOM, FIL ni EOS: la cesta queda en 16 monedas.
  Horquilla (domingo noche): BTC 0,002 %, ETH 0,035 %, SOL 0,043 %, XRP/DOGE 0,16 %, ADA 0,21 %, BCH/AVAX 0,30 %, LTC 0,38 %.
- **Comparación con Python** (mismas D1 FTMO): 2.585 semanas, R media +0,321 en las dos, corr 1,000, máx |ΔR| 0,00005.
  Emparejado 88 % de Python (umbral 90 %): 328 de las 354 que faltan son semanas tras un corte diario del EA y 24 por
  la regla de 60 días; sin esas causas, 99,9 %. **La lógica del EA reproduce Python.**
- **Resultado económico**: +100.095 USD en ~10 años (bruto +152.726, swap −52.631 = 34 % del bruto). **DD máx −21,2 %**
  (oct-2023), peor día −3,8 %, 26 cortes diarios internos del 4 %. Por años: 2017 +24 %, 2018 −8 %, 2019 +8 %, 2020 +21 %,
  2021 +32 %, 2022 −10 %, 2023 +8 %, 2024 +10 %, **2025 −0,4 %, 2026 −5 %**. Exposición media 10 %, máx 58 %.

Lectura: con el riesgo que daba EV positiva en el bootstrap de días (0,2 %/moneda), el DD real de 21 % rompe dos veces
la pérdida total de FTMO (10 %); el bootstrap de días rompía los regímenes de cripto y sobrestimaba el EV. A 0,1 % el DD
sería ~11 % con ~+3,5 %/año: no llega al +10 % de la fase 1 en un plazo razonable. Además la regla de FTMO sobre
apuestas en un solo sentido en símbolos correlacionados es un riesgo de denegación de retiros.

**Veredicto final (22-11-2026, Jorge): DESCARTADO.** Falla en P5 por perfil incompatible con FTMO (DD −21 % con el riesgo que daba EV) y se apaga en 2025-26. No queda en reserva.
