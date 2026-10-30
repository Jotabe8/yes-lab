# IndexBasket v1.00: cómo probarlo

Este EA replica `informes/prima_indices/prima.py`. El EV por cuota de este sistema viene de la estructura de pago de FTMO, no de un edge: lee `RESULTADOS_PRIMA_INDICES.md` antes de usarlo.

## Strategy Tester (MT5 de FTMO)
1. Copia `IndexBasket_v100.mq5` a `MQL5/Experts/`, compílalo en MetaEditor y comprueba que no da errores.
2. En el tester, configura:
   - Símbolo del gráfico: US500.cash, en D1 o H1.
   - Modelado: "OHLC en M1" (con eso basta, porque opera una vez al día).
   - Periodo: 2018.01.01 hasta hoy.
   - Depósito: 200.000 USD, apalancamiento de la cuenta Swing.
3. El EA abre los 6 índices por su cuenta. Si el tester avisa de que falta historia de algún símbolo, descárgala antes desde Ver → Símbolos → Barras.
4. Parámetros:
   - `RiskMult = 1.0`: es el riesgo probado, con una volatilidad de cartera ≈ 7 %.
   - `DailyStopPct = 2.5` en 1-Step (el límite diario es del 3 %); 4,0 en 2-Step.

## Qué comparar con Python (2018-2026, sin dividendos, financiación + 2,5 %)
- Retorno ≈ +0,6 %/año, maxDD ≈ −17 %, volatilidad ≈ 7 %.
- El tester cobra los swaps reales del servidor. Si el retorno sale mucho peor que en Python, la financiación real es más cara de lo supuesto, y eso hay que medirlo.
- Pásame el informe del tester (o el CSV de operaciones). Con él rehago el EV por cuota usando los swaps reales.

## Antes de usar dinero real
- Hace falta una cuenta **Swing**, porque la Standard fondeada no permite mantener posiciones en pausas de más de 2 horas.
- Conviene preguntar a soporte de FTMO si una cesta de índices con volatilidad objetivo está permitida. Lo que preocupa es la regla de "one-sided bets" y de exposición acumulada en símbolos correlacionados.
- Probarlo en demo o Free Trial al menos 4 semanas.
