# De dónde sale el ORB y qué más han publicado sus autores (13-11-2026)

## 1. La fuente del ORB US100

**Zarattini, C. y Aziz, A. (2023). "Can Day Trading Really Be Profitable? Evidence of Sustainable Long-term
Profits from Opening Range Breakout (ORB) Day Trading Strategy vs. Benchmark in the US Stock Market".**
SSRN 4416622 (Swiss Finance Institute Research Paper 23-98). Concretum Group / Bear Bull Traders.

- Regla del artículo: QQQ (y TQQQ), 2016-2023. Si la primera vela de 5 min cierra al alza se compra en la
  apertura de la segunda vela (bajista: se vende); stop en el mínimo (máximo) de la primera vela; objetivo
  10 R; si no salta nada, se cierra al cierre de la sesión. Riesgo 1 % por operación, apalancamiento máx. 4×.
- Resultado publicado: 1.484 % frente a 169 % de QQQ comprado; alfa anual 33 % neto de comisiones.
- Lo confirman las cabeceras de los EAs en el PC (`ORB_US100.mq5` y `ORB_US100_AGR_v018.mq5`: "Modo de
  entrada 0, estilo estudio ORB 5 min en QQQ").
- Nuestra versión cambia dos cosas: el stop a 0,15 ATR (la idea viene del artículo de las acciones "en juego"
  de los mismos autores, que usa un stop del 10 % del ATR) y el filtro de volatilidad p90 de la v018.

Enlaces: [SSRN](https://papers.ssrn.com/abstract=4416622) · [Concretum](https://concretumgroup.com/can-day-trading-really-be-profitable/)

## 2. Todo lo que han publicado (Concretum: Zarattini, Aziz, Barbon, Pagani, Mele) y qué hicimos con ello

| Trabajo | Autores | Qué es | Estado en el proyecto |
|---|---|---|---|
| Can Day Trading Really Be Profitable? (2023) | Zarattini, Aziz | ORB 5 min QQQ | **Es el ORB US100 (funciona)** |
| A Profitable Day Trading Strategy for the US Equity Market (2024) | Zarattini, Barbon, Aziz | ORB en acciones "en juego" | Descartado 13-11 (bruto < coste) |
| Beat the Market: Intraday Momentum for SPY (2024) | Zarattini, Aziz, Barbon | Zona de ruido + VWAP | Descartado 25-10 (se apaga, colas) |
| VWAP, the Holy Grail for Day Trading (2023) | Zarattini, Aziz | VWAP en QQQ/TQQQ | Descartado (sin bruto) |
| Improving Performance with Fast Alphas (2026) | Pagani, Zarattini | Racha de reversión como filtro de entrada de la zona de ruido | T0: no es estrategia nueva (afina una ya descartada) |
| Breaking the Rules of Intraday Trading (2026) | Pagani | Guardar de noche solo los largos | **Probado hoy (§4): descartado** |
| Seasonality in Bitcoin Intraday Trend (2026) | Pagani | Tendencia BTC más fuerte de domingo 19:00 NY a lunes | T0: 52 ops/año → ~30 años para verificarlo (C) |
| Catching Crypto Trends (2025) | Zarattini, Pagani, Barbon | Donchian en conjunto, rotación top-20 cripto, diario | T0: Darwinex solo da BTC/ETH; alfa sobre BTC comprado no verificable con 8 años (C); cesta cripto ya vista como beta |
| The Volatility Edge: VIX ETNs (2025) | Zarattini, Aziz, Mele | Prima de volatilidad (corto VIX con pendiente de la curva) | T0: Sharpe publicado ~1 → 0,5 tras dividir: t 2,1 con 17 años (C); cola de 2018/2020; VIX no está en FTMO y en Darwinex Zero no consta |
| Does Trend-Following Still Work on Stocks? (2025) | Zarattini, Pagani, Wilcox | Tendencia solo larga en acciones | Fuera: cartera de acciones de días/semanas, no prop |
| A Century of Profitable Industry Trends (2024) | Zarattini, Antonacci | Tendencia en 48 sectores | Fuera (igual) |
| GTAA, NextVoL, Tranching, ChatGPT momentum | varios | Asignación de activos / ejecución | Fuera (no son sistemas operables en prop) |
| The Power of Price Action Reading (2024) | Zarattini, Stamatoudis | Trader discrecional filtra huecos | Fuera (discrecional) |
| Martingale (2023) | Zarattini, Aziz | Divulgación sobre estafas | — |

Andrew Aziz además tiene los libros de Bear Bull Traders (ABCD, bandera alcista, rojo a verde, VWAP,
acciones en juego): son patrones discrecionales de acciones ya cubiertos por el ORB de acciones y el VWAP.

Andrea Barbon, en su obra académica: **"Gamma Fragility"** (Barbon y Buraschi, 2021): cuando los creadores
de mercado tienen gamma negativa, el índice sigue la dirección del día en la última media hora. Es
información nueva (no el propio precio), pero T0 la cierra: el efecto publicado es ~SR 1 anual repartido en
252 operaciones (0,06 por operación; 0,03 tras dividir por 2) → más de 35 años para verificarlo aunque se
filtre a días de gamma negativa. Además el dato de gamma (SqueezeMetrics) no se puede bajar desde aquí.

## 3. Autores con el mismo perfil (mecanismo conocido, mercado barato, stop corto) y qué queda

| Trabajo | Idea | Estado |
|---|---|---|
| Holmberg, Lönnbark y Lundström (2013) | ORB en futuros de crudo | Probado (ORB USOIL en 11 mercados): sin edge |
| Crabel (1990) | ORB tras NR7/NR4 | Descartado 30-10 (artefacto Yahoo) |
| Gao, Han, Li y Zhou (2018) | Primera media hora predice la última | Descartado (momentum de cierre) |
| Baltussen, Da, Lammers y Martens (2021) | Cobertura de gamma → momentum de cierre | Igual que Gamma Fragility (T0: C) |
| Heston, Korajczyk y Sadka (2010) | Periodicidad intradía | Descartado 30-10 |
| Lou, Polk y Skouras (2019); Cliff, Cooper y Gulen (2008) | Prima nocturna | B en CFD; **hoy en futuros: descartado** |
| Lucca y Moench (2015) | Deriva pre-FOMC | T0: 8 ops/año (C) |
| Elaut, Frömmel y Lampaert (2018) | Momentum intradía en forex | T0: coste del forex en plazos de horas (B), ya visto en scalping y fix |

**Conclusión: no queda ningún trabajo de estos autores ni de los afines que no esté probado o que pase el
filtro T0.** Lo útil de esta familia ya lo tenemos: el ORB US100 y, en Darwinex Zero, el ORB cripto.

## 4. Prueba de hoy: prima nocturna en futuros de índices US para Darwinex Zero

Preregistro: `PREREGISTRO_NOCHE_FUTUROS.md` (subido antes del cálculo). Script `noche_futuros.py`,
salida `noche_futuros_salida.txt`. M1 Dukascopy en precio medio, US500/US100 desde 2011-09 y US30 desde 2013,
hasta 12-11-2026. Comprar a las 15:55, vender a las 9:30 de la siguiente sesión; rentabilidad tipo futuro
(contado + dividendo − T-bill) y coste de futuros CME (1 tick + comisión: 0,3-0,6 pb).

| Cartera (US500+US100+US30) | Media | Anual | Sharpe | t |
|---|---|---|---|---|
| Noche bruta | 3,1 pb/día | 7,8 % | 0,72 | 2,78 |
| **Noche neta (principal)** | 2,6 pb/día | 6,6 % | 0,61 | **2,36** |
| Noche, costes × 2 | 2,2 pb/día | 5,4 % | 0,50 | 1,94 |
| Placebo intradía 9:30→15:55 | 2,8 pb/día | 7,0 % | 0,55 | 2,13 |
| Placebo siempre comprado | 5,9 pb/día | 14,8 % | **0,89** | 3,44 |

| Criterio | Resultado | ¿Pasa? |
|---|---|---|
| 1. t neto ≥ 2,4 | 2,36 | no (por poco) |
| 2. 2ª mitad > 0 | Sharpe 0,41 (1ª mitad 0,94) | sí, pero a la baja |
| 3. Costes × 2 > 0 | +5,4 %/año, t 1,9 | sí (> 0) |
| 4. Mejor que los placebos | 0,61 < 0,89 del siempre comprado | **no** |
| 5. Sube el Sharpe del ORB ≥ 0,10 y más que el siempre comprado | −0,03 (siempre comprado +0,27) | **no** |

**DESCARTADA.** De 2012 a 2026 la noche ya no se lleva la rentabilidad del índice: la mitad llega de día
(en 2016, 2023 y 2025 casi toda). Guardar solo la noche gana menos por unidad de riesgo que mantener el
futuro todo el tiempo, y mezclada con el ORB no aporta nada. Años malos: 2022 −17 %, 2016 y 2023 ≈ 0.
Nota: el 21-09-2011 hay un salto de +9,6 % en US500 que parece un fallo de datos; quitarlo empeora el
resultado, así que no cambia el veredicto.

Al margen (no era la pregunta): en la misma prueba, el futuro siempre comprado sube el Sharpe del ORB de
1,04 a 1,31 en Darwinex Zero. Ya se miró el 13-11 con una cesta multiactivo (+0,08) y se descartó por ser
beta; este número es solo de US100/US500/US30 de 2018-26 y es mirar atrás en un periodo alcista.

Registro v3: clase B → "Prima nocturna en futuros (Darwinex Zero)": clase A por placebo (no supera al
siempre comprado). No se reabre por ningún lugar: el problema ya no es el coste.
