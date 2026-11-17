# Variables de estado de los sistemas en real (17-11-2026)

Lección de la deriva nocturna de futuros US (NY Fed, *The Disappearing Overnight Drift*, julio 2026): la ventaja murió desde 2021 porque cayó su causa, el desequilibrio de órdenes al cierre, y eso se veía en la causa antes que en los resultados. Cada sistema en real tiene que nombrar la variable que explica su ventaja y vigilarla junto a la R media.

| Sistema | Mecanismo | Variable de estado | Cómo se mide | Alarma |
| --- | --- | --- | --- | --- |
| ORB US100 v018 | Desequilibrio de la apertura de NY que continúa (Zarattini-Aziz) | Continuación del rango: fracción de días con ruptura del rango de 10 min que llegan a +1 R a favor antes del stop | Velas M1 del día; también la cuenta de días que pasan el filtro de volatilidad p90 | Media móvil de 60 días con señal por debajo del p10 del backtest 2018-26 |
| ORB en juego v13 | Días con rango de apertura ≥ 1,5× su media atraen flujo que continúa | Igual que arriba en GER40/UK100/JP225/oro/crudo, solo días en juego | M1 Dukascopy/ticks FTMO | Igual |
| Reversión DZ | Liquidez que se paga tras cierres débiles (IBS < 0,2) en índices US | Rebote medio a 1-5 días tras IBS < 0,2 en ES/NQ/YM, en R de ATR | D1, independiente de que el EA opere | Media móvil de 12 meses por debajo de 0 |

Estado: propuesta. El informe diario (23:05 Madrid) no se ha tocado. Para añadirlo hace falta el cálculo en el PC (velas M1 del día) y el p10 de referencia de cada sistema, que se calcula una vez con los datos del backtest.
