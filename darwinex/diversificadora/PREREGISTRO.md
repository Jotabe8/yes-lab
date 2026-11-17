# Preregistro: pata diversificadora para el DARWIN del ORB US100 (16-11-2026)

Escrito antes de bajar los datos de futuros y antes de calcular nada. Pregunta de Jorge: una estrategia, en cualquier
mercado, que diversifique el riesgo de una cuenta de Darwinex Zero que lleva el ORB US100 v018.

## Qué cambia respecto a lo ya probado

- El 13-11 se probaron momentum 12 m (B) y cesta siempre comprada (C) con índices, forex y metales, y se juzgaron
  **como estrategias con ventaja propia**. C era beta (Sharpe 0,71) y con el ORB subía el Sharpe de 1,38 a 1,46 solo
  con el peso elegido a posteriori (a igual riesgo, 1,34). C no tenía bonos y el "largo en forex" no es una prima.
- Aquí la pregunta es otra: si una pata **sin ventaja propia, solo primas de riesgo**, mejora el DARWIN conjunto de
  forma robusta, con el peso fijado antes y con la prima recortada. Si no lo hace, se descarta igual.
- Solo cabe en la **cuenta de futuros** de DZ (sin swap). En la cuenta CFD el swap largo del NDX es −45 $/día por
  contrato (~6,5 %/año del nominal), que se come cualquier prima. Por tanto el ORB iría en el NQ.

## Pata principal (P): paridad de riesgo simple en futuros de DZ

- Mercados: ES (acciones EE. UU.), ZN (bono 10 años), GC (oro). Las tres primas con más historia publicada.
- Pesos: igual riesgo por mercado con volatilidad EWMA de 60 días; se decide al cierre de mes y se aplica al día
  siguiente. La pata se escala a 10 % de volatilidad anual con la volatilidad realizada de 1 año (tope ×3).
- Rendimientos: futuros continuos de Yahoo. Los saltos de roll se sustituyen por el rendimiento del sustituto al contado
  (ES ↔ ^GSPC, GC ↔ XAUUSD, ZN ↔ −6,5 × ΔDGS7 + carry) en los días en que la diferencia futuro − sustituto supere
  4 desviaciones típicas de esa diferencia.
- Costes: 2 pb del nominal por cada unidad de giro, más 2 pb del nominal por roll (4 al año en ES y ZN, 6 en GC).

Variante informativa (P4): añade una cuarta clase, materias primas (CL y HG a igual riesgo entre sí), con días de
roll excluidos por calendario. No decide.

## Cómo se combina con el ORB (fijado antes)

- Serie del ORB: `serie_v018_be.csv` (Rbe − 0,05 R), mensual, 2018-01 → 2026-10.
- **Peso fijo:** la volatilidad mensual de la pata = 0,5 × la del ORB. Luego la mezcla se reescala a la volatilidad del
  ORB solo (Darwinex reescala a VaR objetivo). 0,5 es el cociente de Sharpe esperado (≈0,6 / ≈1,3), elegido sin mirar.

## Criterios para aceptar la pata (todos)

1. Pata sola 2002-2026 neta: t ≥ 2,0 (es beta, se espera que lo cumpla) y Sharpe 2018-26 > 0.
2. Correlación mensual con el ORB 2018-26 ≤ 0,20.
3. DARWIN mezcla frente a ORB solo, 2018-26: **Sharpe mensual +0,10 o más**, peor DD (a igual volatilidad) no peor,
   y % de ventanas de 6 meses positivas no menor.
4. Con la prima de la pata **recortada a la mitad** (media × 0,5): Sharpe de la mezcla sigue por encima del ORB solo.
5. Bootstrap por bloques de 3 meses de los meses conjuntos (10.000): P(ΔSharpe > 0) ≥ 80 %.
6. Monte Carlo de 36 meses de `dz_sim` (el mismo de los informes anteriores): neto €/año de la mezcla en la cuenta de
   futuros (50 €/mes) mayor que el ORB solo en la cuenta CFD (35 €/mes), con y sin permanente +10 %.

## Placebos y controles (informan, no deciden)

- Pata con media cero (rendimientos menos su media): mide cuánto del efecto es cobertura y cuánto es prima.
- Desfase aleatorio de la pata frente al ORB (1.000 desplazamientos circulares de meses): dónde cae el ΔSharpe real.
  Si cae en la cola alta, la baja correlación de 2018-26 fue suerte.
- 2012-2026 con la réplica del ORB (`historia-2012/orb_us100_2012_2026.csv`, bruto − 0,05 R).

Si falla cualquiera de 1-6, la pata se descarta y no se escribe EA.
