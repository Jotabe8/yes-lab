# v17 — Qué mejora de verdad el método de búsqueda (20-11-2026)

Pedido de Jorge: buscar en internet cómo mejorar la búsqueda de estrategias, ponerlo a prueba y repetir.
Banco de pruebas propio: **4.284 reglas diarias reales** (9 familias con rejilla × 2 lados × 37 mercados:
índices, divisas, energía, metales, agrícolas, bonos; `cohorte.py`), ajuste 2001-14 y fuera 2015-26, y otra vez con
ajuste 2001-10 y fuera 2011-26. Objetivo principal: R **sin deriva** (`tx`, lo que mide el placebo); secundario:
con exposición (`t`). Control positivo: IBS largo en índices US (la reversión DZ). Criterio en `PREREGISTRO.md`.

## Resultado en una tabla

| Ronda | Idea (fuente) | Resultado | Veredicto |
| --- | --- | --- | --- |
| 1 | Meseta: media de la regla y sus vecinos de rejilla (AlgoXpert arXiv 2603.09219, foros) | Spearman con el fuera +0,02-0,03 sobre el t (IC excluye 0 en `tx` en los dos cortes), pero el top 5 % no mejora en 2011 | Marginal: no cumple el criterio completo. No se añade puerta |
| 1 | Misma regla en otros mercados de la clase (foro MQL5 "instrumento relacionado") | Peor que el t solo en el top (+0,17 vs +0,29) | Descartada sola |
| 1 | Estabilidad (peor de las dos mitades del ajuste) | = t | Descartada |
| 1 | Walk Forward Correlation (Tinsley 2026) | Spearman ≈ 0 o negativa, IC del Δ por debajo de 0 en los 4 casos | Descartada |
| 1 | Volatilidad y DD del ajuste (Wiecki et al. 2016, R² 0,67 y 0,34) | Predicen la volatilidad fuera, **no** la ventaja (Spearman 0,02-0,07) | No sirve para elegir |
| 2 | Encogimiento empírico (Chen-Dim 2025, Harvey-Liu 2015) | Las reglas con t ajuste ≥ 3 retienen **el 26 %** del t fuera sin deriva (3,55 → 0,92 y 3,33 → 0,86); con exposición 32-51 % | **Sirve**: el recorte del embudo con n=10 promete 2,6 y sale 0,9; con N = todo lo mirado (4.284) promete 0,96 / 0,74 → cuadra |
| 3 | Prueba de ruido en el OHLC (Build Alpha, StrategyQuant, QuantConnect) | t con ruido corr 0,91-0,95 con el limpio; no predice mejor (Δ −0,01, IC ≤ 0); "fragilidad" peor que nada | Descartada |
| 4 | BHY / BH global (Harvey-Liu recomiendan BHY) | En el corte 2011 no deja pasar **nada**, ni el control positivo IBS-US (que fuera da t +1,8-2,8) | Demasiado estricta para nuestro uso |
| 4 | Bonferroni n=100 (t ≥ 3,29) frente a n=10 (t ≥ 2,58) | t > 1 fuera: 50-80 % frente a 38-44 % (`tx`); 79-89 % frente a 52-72 % (`t`) | El listón real está en t ≈ 3,3, no en 2,6 |
| 4 | Juzgar la FAMILIA (media de todas las variantes) y no su mejor variante (Chen-Dim, EB) | Spearman con el fuera de la familia 0,40-0,60 (media) frente a 0,02-0,42 (mejor variante) en 102 familias, 4 de 4 casos | **Sirve** como aviso (ver límite abajo) |
| 5 | PBO/CSCV, que en el embudo BLOQUEA si > 0,5 (Bailey et al.) | Spearman con el fuera de la elegida −0,07 / −0,11; con t ≥ 2,58 casi nunca pasa de 0,5 (0-1 de 17) y no ordena | Redundante con el t; se deja como está |

## Qué se aplica al embudo (`metodo/embudo.py`, avisos que no bloquean)
1. **"libro de pruebas"**: si se llama sin `familia=`, avisa. El libro del PR #52 no se había usado ni una vez
   (no existe `metodo/libro/`): v13-v16 contaron n_pruebas a mano. La ronda 2 muestra que el recorte solo cuadra
   cuando N es todo lo mirado.
2. **"media de la familia"**: con `variantes=`, t medio de todas las variantes frente a la mejor.
   Límite: una ventaja estrecha y real puede tener media ≈ 0 en su familia (el ORB US100 dentro de "ORB en todos
   los mercados": GER40, cripto y Asia no tienen ventaja). Por eso es aviso y la familia se define por mecanismo y
   mercado, no "la idea en todas partes".

## Qué cambia en la práctica
- Contar como n_pruebas **cada casilla mirada** (mercado × parámetro × lado × horario), por eso el libro.
- Para una regla salida de un barrido, esperar fuera ≈ ¼ del t de ajuste sin deriva. Una regla con t 3 de un
  barrido grande vale t ≈ 0,8 fuera: no merece P2-P4 si no hay mecanismo y réplica.
- Los descartes de ruido, WFC, estabilidad por mitades y vol/DD no se añaden: no predicen nada en datos reales.

## ¿Reabre algo?
Ningún descarte. Subproducto del mapa (no es una prueba de sistema): **vender gasolina RB el lunes** (posición del
cierre del viernes al del lunes) es la regla nº 1 del ajuste sin deriva (t 4,88, pasa Bonferroni con N = 4.284) y
fuera da t 2,47 (2015-26); en el otro corte 4,08 → 3,51. ≈ +0,07-0,13 R por operación, 52 ops/año, coste 0,02 R.
Gasóleo HO igual de signo y más débil; crudo no. Solo candidato a preregistro si el mercado existe en Darwinex Zero
(FTMO no tiene gasolina). Lo demás que aguanta (3 días bajistas → largo en índices US) es la reversión DZ ya vigente.

## Fuentes
Wiecki et al. 2016 (888 algoritmos Quantopian; resumen Quantpedia y CXO): Sharpe de ajuste R² < 0,025.
Chen y Dim 2025, arXiv 2311.10685 (136.000 estrategias, EB). Harvey y Liu 2015 "Backtesting" (haircut no lineal,
BHY). AlgoXpert arXiv 2603.09219 (meseta 0,9·SR óptimo). Tinsley 2026 (Walk Forward Correlation). Build Alpha
(noise test, seeitmarket 2017), QuantConnect foro 21206 (perturbar precios). Foros StrategyQuant y MQL5 515330:
solo anécdotas, sin cifras.

Archivos: `cohorte.py`, `analizar.py`, `ronda2.py`-`ronda5.py`, `ruido.py` y sus `*_salida.txt`.
