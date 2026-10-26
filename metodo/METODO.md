# Método para crear EAs (versión 1, 2026-10-26)

Objetivo: decidir en horas, no en días, si una idea merece un EA, y que las que lleguen a MT5
tengan muchas más probabilidades de sobrevivir. Criterio final: **EV por cuota en FTMO 2-Step
por encima del control sin edge** y correlación baja con el ORB US100.

## 1. Qué nos ha enseñado este proyecto

- Más de 20 familias probadas desde el 2026-10-24; solo sobreviven el ORB US100 y el ORB GER40.
- Los efectos publicados ganan 0,02-0,05 % por operación, lo mismo que cuesta un CFD de prop.
  **El coste en R decide antes que la idea.**
- Dos pérdidas de tiempo repetidas: (a) escribir el EA antes de probar la regla en otros
  mercados (GER40 EMA20 murió después, en 14 mercados); (b) no comparar con un placebo con las
  mismas salidas (la dirección aleatoria daba +0,10 R: el edge era el corredor, no la entrada).
- Una cartera de retos tiene EV positivo incluso sin edge por la estructura de FTMO
  (control de la cesta de índices, `ea-indices/` en los archivos del proyecto). Un EA solo vale si **supera ese control**.

## 2. Qué hacen los que lo consiguen (resumen de la investigación)

| Fuente | Idea que adoptamos |
| --- | --- |
| Kevin Davey (*Building Winning Algorithmic Trading Systems*; biblioteca de 200 estrategias, unas 20 activas) | Prueba de viabilidad corta antes de nada; entrada y salida se prueban por separado; walk-forward, Monte Carlo e incubación de 3-12 meses; cartera de sistemas en sectores distintos y rotación mensual. |
| StrategyQuant (flujo oficial) | Generar, filtrar y luego "cross-checks": otros mercados, otros marcos temporales, spread/slippage peores, datos de mayor precisión (ticks reales), Monte Carlo y matriz walk-forward. |
| Build Alpha (prueba de ruido) | Volver a simular sobre 1.000 series con ruido añadido; si la original es mucho mejor que las ruidosas, está sobreajustada. |
| Bailey, Borwein, López de Prado y Zhu (2014) | Con más de 45 variantes en 5 años de datos es casi seguro sacar un Sharpe 1 en muestra con Sharpe 0 real. **Hay que contar los intentos.** |
| Harvey y Liu (*Backtesting*, 2015) | Recortar el Sharpe según el número de pruebas; las estrategias marginales caen; t ≥ 3 cuando se han mirado muchas. |
| Artículos de MQL5 sobre límites diarios en prop | Día por la hora del servidor, base = máx(balance, equity) al empezar, medir equity en cada tick, estado que sobreviva a reinicios, corte interno por debajo del de la firma. |

## 3. El embudo

Cada puerta tiene un tiempo máximo. Si no se pasa, **se descarta y se anota** en `DIARIO.md`
y en la memoria (regla de Jorge: no se deja nada "en reserva").

| Puerta | Tiempo máx. | Qué se hace | Se descarta si |
| --- | --- | --- | --- |
| **P0 Ficha** | 10 min | Hipótesis causal (quién pierde dinero y por qué), mercado, marco, ops/año esperadas, stop típico, **coste en R** = (spread + comisión) / stop con datos bid/ask. Mirar la lista de descartados de la memoria. | Ya está descartada; coste > 0,10 R; < 40 ops/año; o el efecto publicado es < 3 × coste. |
| **P1 Prueba rápida** | 1 h | Regla fija, sin optimizar, salida simple (N velas o stop/objetivo fijos). Ajuste 2018-2022. **A la vez en 3-5 mercados parecidos.** Placebo con las mismas salidas (dirección o hora aleatoria, 200 réplicas). | Bruto < 3 × coste; no supera el p95 del placebo; funciona en un solo mercado. |
| **P2 Neto y estabilidad** | 2 h | Costes reales y al doble; años positivos; meseta de parámetros (vecinos ±20 % conservan la mitad del edge); prueba de ruido. | Neto ×2 ≤ 0; < 60 % de años positivos; pico aislado de parámetros; < 90 % de réplicas con ruido > 0. |
| **P3 Fuera de muestra** | 30 min | Se abre **una vez** 2023-2026. t total contra el t corregido por número de pruebas (tabla abajo). | OOS ≤ 0 o t OOS < 1; t total < t requerido. |
| **P4 Prop** | 30 min | EV/cuota 2-Step (Monte Carlo por días) frente al control sin edge; correlación diaria con el ORB US100. | EV ≤ control; correlación > 0,3. |
| **P5 MQL5** | 2 h | EA desde `PlantillaPropEA.mq5`, solo con lo probado. Strategy Tester con ticks reales de FTMO en el mismo periodo. | Ops o R media a más de ±20 % de Python (primero se busca el fallo; si es del modelo, se descarta). |
| **P6 Incubación** | 4-8 semanas | Demo o Free Trial de FTMO, sin tocar nada. | Resultado fuera de la banda del Monte Carlo (p5-p95). |

`metodo/embudo.py` automatiza P1-P4 con una tabla de operaciones (fecha, R bruta, coste en R):

```python
from metodo.embudo import embudo
print(embudo(ops, n_pruebas=24, corte_oos="2023-01-01", placebo=sim_aleatoria,
             ev_control=1569))
```

**t requerido según el número de variantes miradas** (una cola, 5 %, Bonferroni):
1 → 1,64 · 10 → 2,58 · 50 → 3,09 · 100 → 3,29 · 1.000 → 3,89 · 25.000 → 4,6.
Cuenta todo: parámetros, mercados, horarios y salidas probados, aunque no se presenten.

## 4. Reglas para ir rápido

1. **Preregistro de 5 líneas** antes de mirar datos: regla, mercados, periodo, métrica, umbral.
2. Una idea por hilo y presupuesto de tiempo; si una puerta se alarga el doble, se para.
3. Primero el bruto en varios mercados, después los detalles. Nunca al revés.
4. Siempre un control: placebo con las mismas salidas y, en P4, la cesta sin edge.
5. Nada de rescates: si falla, no se añaden filtros para salvarla (eso suma pruebas).
6. El EA se escribe después de P4. El Strategy Tester confirma la simulación, no la descubre.
7. Datos: M1 bid/ask de Dukascopy (hora servidor = NY+7) y ticks de FTMO; D1 de
   `data/ohlc`, no de `data/dukascopy` (corruptos).

## 5. Dónde buscar (más probabilidad por hora invertida)

Lo que tiene más opciones frente al coste de un CFD: **operaciones con recorrido grande en R
(stop amplio respecto al spread), pocas por día, en horas de liquidez**, y efectos causados
por **flujos obligados** (alguien tiene que comprar o vender pase lo que pase), no por
patrones de precio.

Candidatas no probadas en este proyecto, en orden:

1. **Rebalanceo institucional 60/40** (Harvey, Mazzoleni y Melone, NBER 33554, 2025). Si las
   acciones han batido a los bonos en el mes, los fondos venden acciones en la última semana
   y el índice cae; al revés, sube. Réplica independiente: Sharpe > 1,4 en futuros, beta 0,07.
   Es **condicional** al rendimiento relativo, distinto del "cambio de mes" ya descartado.
   Se prueba en US500/US100 (y GER40) solo con la pata de acciones; bonos de FRED (DGS10)
   con el workflow `descargar-macro.yml`. Riesgo: ~5-10 ops/año, quizá pocas para un reto.
2. **Deriva previa al FOMC condicionada a volatilidad alta** (Lucca y Moench; Quantpedia:
   ~109 pb con la volatilidad implícita por encima de la mediana frente a ~10 pb por debajo).
   8 ops/año: solo como complemento de cartera, nunca como EA principal.
3. **Ideas generadas en masa con corrección honesta**: si se hace una búsqueda amplia (tipo
   StrategyQuant), fijar antes el número de variantes y exigir el t de la tabla; la
   búsqueda de 25.000 reglas intradía ya se hizo y no dejó supervivientes, así que solo
   tiene sentido en un espacio nuevo (otros marcos o eventos).

Ya descartadas (no repetir): ver la memoria del proyecto; incluye reversión a la media, RSI(2),
momentum de cierre y de última media hora, cambio de mes, trend following y TSMOM, noticias,
VWAP, ORB fuera de US100/GER40, pares, BTC intradía, prima nocturna, Halloween, carry/COT,
Bollinger en oro, Supertrend, pullback de Pons, NNFX D1, entrada aleatoria, scalping M1-M15 y
EMA20 GER40.

## 6. Plantilla MQL5

`metodo/PlantillaPropEA.mq5`: solo se rellena `Senal()` (y `Gestionar()` si hay
break-even o trailing). Ya incluye:

- Lotes por % de riesgo con `OrderCalcProfit` (redondeo hacia abajo; no abre si el stop no cabe).
- Corte diario interno (4 % del balance inicial desde la base del día) y total (8 %) con
  estado guardado en variables globales: sobrevive a reinicios del terminal.
- Parada al alcanzar el objetivo del reto, horario de entradas, cierre a una hora o el viernes,
  máximo de operaciones por día, filtro de spread, un mágico por EA y símbolo.
- CSV de operaciones cerradas en `Common/Files` para comparar con Python en P5.

No está compilada en este entorno: compilar en MetaEditor y corregir avisos antes de usarla.

## Fuentes

- StrategyQuant, flujo de trabajo: https://strategyquant.com/doc/strategyquant/workflow/
- Prueba de ruido de Build Alpha: https://seeitmarket.com/?p=48626
- Bailey et al., sobreajuste por iteración: https://www.cxoadvisory.com/big-ideas/insidiousness-of-overfitting-investment-strategies-via-iterative-backtests
- Harvey y Liu, *Backtesting* (resumen de Man Group): https://www.man.com/insights/backtesting
- Deflated Sharpe Ratio: https://papers.ssrn.com/abstract=2460551
- Kevin Davey: https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about
- Límite diario en un EA de prop: https://www.mql5.com/en/blogs/post/777235
- Rebalanceo institucional: https://www.nber.org/papers/w33554 y https://quantreturns.substack.com/p/front-running-the-rebalancers
- Deriva pre-FOMC: https://quantpedia.com/?p=4197
