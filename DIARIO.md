# Diario de pruebas de estrategias

Cada semana la rutina "Estrategias de trading semanal" recopila estrategias con evidencia
publicada (informe en `trading/research/semanal/` de los archivos del proyecto), elige una o
dos y las prueba aquí en simulación. Las entradas más recientes van arriba. Nada de esto es
una recomendación de inversión.

Convenciones: datos diarios de `docs/data/`, señal al cierre y ejecución en la sesión
siguiente, solo largo, costes por lado normales y al doble, walk-forward con 3 años de
ajuste y 1 de prueba. El código está en `lab/estrategias.py`.

| Fecha | Estrategia | Mercados | Veredicto |
| --- | --- | --- | --- |
| 2026-11-22 | v19 tendencia semanal en cesta cripto (`metodo/v19/`): comprado si rendimiento 28 d > 0, tamaño 1/σ, rebalanceo dominical, preregistrada, n_pruebas 15, t por semana | 20 monedas Binance 2019-26 + réplica 126 | **Pasa P0-P4 en FTMO** (neto +0,166 R t 2,48, fuera t 1,23; EV/cuota 2-Step a 0,2 %/moneda +6.274 € vs beta +3.471 € vs control +1.413 €) y en exchange (t 3,19); **falla P4 en Darwinex Zero** (Sharpe DARWIN 1,92→1,96). Banderas: exceso sobre la beta fuera t 0,97, 2025-26 ≈ 0/negativo, sin deriva Sharpe 2023+ 0,27. Corr ORB −0,07, reversión +0,11. Decide Jorge si pasa a P5 |
| 2026-11-20 | Revisión del filtro de volatilidad p90 del ORB US100 (`metodo/filtro_vol/`), preregistrada, 3 pruebas, t por semana y placebo de racimos | US100 2012-26 | **Mantener filtro y tope de 21 días**: días bloqueados neto −0,010 R (t −0,09, 392 ops), pausas ≥ 10 días −0,02 R; el filtro no sube R/año (+0,3) pero baja el peor DD 48,5 → 37,6 R (más que el placebo p5) |
| 2026-11-20 | v17 método (`metodo/v17/INFORME.md`): qué métrica del ajuste predice el fuera, en una cohorte de 4.284 reglas diarias reales (9 familias, 37 mercados, cortes 2015 y 2011); ideas de internet: meseta, WFC, ruido OHLC, EB, BHY, familia, PBO | 37 mercados diarios | Sirven: encogimiento (t ≥ 3 retiene 26 %; recorte cuadra solo con N real) y media de la familia (Spearman 0,40-0,60 vs 0,02-0,42); descartadas: ruido, WFC, estabilidad, vol/DD, BHY; meseta marginal; PBO redundante. Avisos nuevos en el embudo |
| 2026-11-19 | Compras de fin de mes en bonos: auditoría, P4 en Darwinex Zero y réplica en el Bund, preregistrado (`darwinex/bonos_fin_de_mes/`) | ZN real (Yahoo, rolls limpios), Bund 10 a (Bundesbank) | **Descartada**: cifras del informe reproducidas y placebo completo limpio (fin de mes +24 pb vs resto ≤ +8,6), pero el ZN rinde el 70 % y 2019-26 t 1,93; DARWIN 1,72 → 1,90 con DD 20,6 → 22,1 R (criterio 2 falla), ventaja a la mitad 1,74; Bund neto t 1,76 y 2019-26 negativo |
| 2026-11-17 | Reversión de varios días en índices para Darwinex Zero (`darwinex/reversion_dz/`): IBS < 0,2 y cierre bajista → largo al cierre, salida cierre > máximo de ayer o 5 sesiones, sin stop, preregistrada, 2003-26 | ES, NQ, RTY, YM (réplica DAX, Euro Stoxx) | **PASA P0-P4** (n_pruebas 10): neto +0,236 R t 8,4 (2003-22), placebo de exposición p95 +0,128 vs +0,261 bruto, 2023-26 neto +0,270 t 4,4; futuros con entrada 18:00 t 5,9; corr ORB −0,02, Sharpe DARWIN 1,04 → 1,72. No se replica en Europa; cola −10,6 R (feb-2018). Pendiente P5-P6 |
| 2026-11-16 | v15 otras matemáticas (`metodo/v15/`): valor relativo intradía con beta de Kalman y choques endógenos/exógenos con Hawkes, preregistradas; HMM, entropía, wavelets, valores extremos, recurrencia y CUSUM fuera en T0 | US100, US500, US30, GER40 (M1 2012-26) | Descartadas (clase A): Kalman bruto −0,028 R neto t −2,8, 0/3 pares; Hawkes bruto +0,005 R neto t −2,7, 0/4 mercados; motores limpios |
| 2026-11-16 | ORB en juego en aperturas propias (`metodo/v13/`): rango (V2) o volumen (V1) de los 10 primeros min ≥ 1,5× su media, M1 Dukascopy 2012-26, coste FTMO | GER40, UK100, JP225, oro, crudo | **V2 PASA** (neto +0,200 R t 3,35, placebos, ×2, 5/5 mercados, corr v018 −0,01); V1 no (t 2,27). Pendiente P4-P6 |
| 2026-11-16 | Mejor descartado recalculado para Darwinex Zero (`darwinex/mejor_descartado/`): gotobi USDJPY (CFD DZ 1,15-1,55 pips, 6J) y ORB GER40 (FDAX) | USDJPY, GER40 | Ninguno revive: gotobi neto t 1,1-2,2 y ×2 < 0 (la comisión DZ sola son 0,75 pips); ORB GER40 t 2,24 incluso sin coste |
| 2026-11-16 | Compras de duración de fin de mes en bonos (Hartley-Schwarz), preregistrada (`darwinex/PREREGISTRO_BONOS_FIN_DE_MES.md`), 1990-2026 | 10 años (ZN), 5 y 30 años informativos | **Pasa** la principal: neto +21,6 pb/op t 5,6; 2019-26 t 2,5; placebo mitad de mes t 1,3; futuro ZN real neto t 4,1. Falla la secundaria: los meses de refinanciación no rinden más en 1990-2015. Solo Darwinex Zero (FTMO no tiene bonos); 12 ops/año |
| 2026-11-15 | v10-bis: volumen con signo de QQQ 9:30-9:40 (Alpaca SIP, regla del tick) como filtro del ORB v018 (`metodo/v10/RESULTADOS_V10_BIS.md`) | QQQ/US100 | Descartado: dif acuerdo − desacuerdo +0,03 R (t 0,29), 2022-26 negativa, bajo el placebo |
| 2026-11-17 | Mejoras del embudo tras investigar evaluación honesta (`metodo/METODO.md` §3): t por semana, libro de pruebas, nulos GARCH/régimen, prueba de fuga, ventajas plantadas | Reversión DZ, ORB en juego, sintéticos | Reversión DZ t 9,42 → 5,70 (sigue pasando); ORB en juego 3,35 → 3,25; P1 con 2018-22 solo detecta el 25 % de ventajas +0,10 R a 80 ops/año (45 % con 2011-22): P1 pasa a toda la historia |
| 2026-11-14 | Tendencia de largo plazo con gestión NNFX (Donchian 55/100, cruce 50/200; stop 1,5 ATR, mitad a 1 ATR, BE, salida canal), preregistrada, 2005-26 (`tendencia_nnfx/`) | 11 pares forex D1 | Descartada: V1 neto −0,001 R t −0,04 (bruto +0,049, swap −0,039); 2016-26 negativo en las 3 variantes (t ≈ −2); bajo p95 del placebo |
| 2026-11-14 | Revisión de descartados con historia larga (`metodo/revision/`): triaje de 72 familias → 2 re-pruebas preregistradas (t ≥ 2,64) | USDJPY/EURJPY/GBPJPY 2003-26, USOIL 2011-26 | Ninguna revive. Gotobi: efecto real (bruto +0,11 R, t 4,4 en 2003-17 nunca visto) pero neto t 1,56; reabrir si coste ≤ 0,8 pips. EIA: ruido (t bruto 1,4, bajo placebo) |
| 2026-11-14 | Zona de ruido Zarattini en Europa (`metodo/v8/PREREGISTRO_ZONA_RUIDO.md`), M1 Dukascopy 2013-26, coste FTMO | GER40, UK100 (EU50 réplica) | No pasa: cartera neto +0,002 R t 0,16; GER40 solo neto t 1,61 (×2 t 0,86); UK100 y EU50 sin bruto; corr ORB 0,03 |
| 2026-11-14 | Búsqueda en internet (`metodo/v8/INFORME_BUSQUEDA_INTERNET.md`): rebalanceo por umbral 60/40 (Harvey-Mazzoleni-Melone 2025) | US500, ZN | No pasa: replica el paper (neto t 3,3 en 2000-26) pero tramo no visto 2023-26 −9,7 pb/op, 25 ops/año; intradía sin swap t 1,8 |
| 2026-11-14 | Revisión 2 de descartados con el motor nuevo (paseo aleatorio en gotobi, EIA, ORB GER40, ORB JP225 y subastas; auditoría de código de las clases B y D) | varios | **Ninguna revive**: motores limpios (sesgo ≈ 0, ninguno negativo); la única regla pesimista (ORB acciones) no pudo esconder ventaja. `metodo/revision2/` |
| 2026-11-14 | Scalping a favor de tendencia fuera de la hora del ORB (`metodo/scalping-v2/PREREGISTRO_TENDENCIA.md`): retroceso EMA20 M5 en día de tendencia, ruptura de microrango | US100, US30, US500, GER40 | Descartado: 0/24; mejor +0,07 R t 1,3 agrupado (igual que el paseo aleatorio); corr ORB ≤ 0,07 |
| 2026-11-14 | Scalping v2 (`metodo/scalping-v2/`): barridos de liquidez, desvanecer el primer impulso de la apertura (M1 y ticks GER40 30 s), números redondos intradía | US100, US30, US500, GER40 | Descartado: 0/60 casillas; mejor t 1,5 bajo placebo; coste 0,05-0,07 R/op y bruto en prueba −0,04 a +0,03 R |
| 2026-11-15 | v10 datos nuevos y sitio barato (`metodo/v10/INFORME_V10.md`): horquilla real USDJPY medida para gotobi; 3 hipótesis preregistradas con desequilibrios de subasta Nasdaq y delta NQ (Databento) | USDJPY, NQ, QQQ | Gotobi cerrado (horquilla 0,76 pips sola, IBKR ≈ 1,35 total); H1-H3 pendientes de la clave de Databento |
| 2026-11-14 | Búsqueda v9 (`metodo/v9/INFORME_V9.md`): ruptura en el dato programado (NFP/IPC/FOMC) y dólar tras el fix del BCE, preregistradas; 18 familias más en T0 | Oro, EURUSD, GBPUSD, USDJPY, US100, US500 | Ninguna pasa: ruptura bruto +0,000 R (evento − placebo t 0,15); fix BCE bruto +0,04 pb; el resto cae en T0 |
| 2026-11-13 | Búsqueda v4 sin restricciones (`metodo/v4/BUSQUEDA_V4.md`): auditoría (8 fallos) + 10 primas con pagador preregistradas | VX, cripto, ETF, bonos, acciones | Ninguna pasa: carry cripto real pero agotado desde 2025; subastas del Tesoro pasan t y réplica pero DD 4,6× y se apagan desde 2016 |
| 2026-11-13 | Reversión tras choques de 5 min (provisión de liquidez, v3) | US100, US500, US30, GER40 | Descartada: 3.610 choques, neto −0,06 R (t −4,2); los choques no revierten |
| 2026-11-13 | ORB GER40 con coste real FTMO 0,0052 % (v3, 2013-26, precio medio) | GER40 | No pasa: neto +0,069 R t 1,58 (<2,4); supera placebos, corr US100 0,00, pero edge demasiado pequeño e irregular (7/13 años +) |
| 2026-11-13 | Lugares para las ventajas de clase B (FundingPips, Topstep MBT/MET/NKD, CME estándar) con costes publicados (v3) | BTC, ETH, JP225 | Ningún lugar accesible las hace operables (t ≤ 1,8; ventaja menor en 2024-26) |
| 2026-11-13 | Stop ancho (0,30 ATR / extremo del rango) en JP225 y ETH (v3) | JP225, ETH | Descartado: bruto y coste en R bajan a la par (la ventaja es fija en precio); t ≤ 1,7 |
| 2026-11-13 | ORB apertura propia en Asia, agrupado (v3, horquilla FTMO real) | JP225, HK50, AUS200 | Descartada: cartera neto +0,008 R t 0,3; JP225 bruto real (t 3,3) pero coste 0,09 R (clase B) |
| 2026-11-13 | Búsqueda v3 (`metodo/BUSQUEDA_V3.md`): potencia del embudo, registro de 60 ideas, triaje T0; ORB cripto en futuros CME | BTC, ETH | Edge real (t 3,0, corr 0,08 con ORB) pero sin lugar operable hoy: clase B con disparador anotado |
| 2026-10-26 | Rebalanceo 60/40 de fin de mes (con el embudo de `metodo/`) | US500, US100, US30, US2000, GER40, UK100, EU50 | Descartada en P0/P1: bruto 1,3× coste, bajo el placebo; ver `metodo/METODO.md` §7 |
| 2026-10-01 | Cambio de mes | SPY, IBEX, SAN, BTC | Descartada: sin efecto medible en 2016-2026 |

---

## 2026-11-16 · Compras de duración de fin de mes en bonos (preregistrada)

**Hipótesis.** El último día hábil del mes los índices del Tesoro incorporan las emisiones nuevas y alargan su
duración; los fondos indexados compran duración y los bonos suben en las últimas sesiones (Hartley y Schwarz, 2019,
muestra 1990-2018). La rutina semanal lo vio en 2016-2026 con IEF y TLT, más fuerte en los meses de refinanciación.

**Regla y criterio.** Preregistrados antes de ejecutar (`darwinex/PREREGISTRO_BONOS_FIN_DE_MES.md`): largo del
10 años las 3 últimas sesiones del mes, coste 3 pb (×2 = 6 pb), precio a partir de FRED como en `bonos_dz.py`.

```bash
python darwinex/bonos_fin_de_mes.py datos_bonos
```

**Resultados** (`darwinex/bonos_fin_de_mes_salida.txt`, pb por operación):

| Tramo | n | Bruto (t) | Neto (t) | Costes ×2 |
| --- | --- | --- | --- | --- |
| 1990-2026, principal | 442 | +24,6 (6,4) | +21,6 (5,6) | +18,6 |
| Placebo: 3 sesiones hasta la 12.ª | 442 | +8,1 (2,0) | +5,1 (1,3) | +2,1 |
| 2019-2026, fuera de la muestra publicada | 94 | +21,2 (2,9) | +18,2 (2,5) | +15,2 |
| Exceso sobre la letra a 3 meses | 442 | +21,3 (5,5) | +18,3 (4,8) | +15,3 |
| Futuro ZN continuo real, 2000-2026 | 312 | +17,1 (5,0) | +14,1 (4,1) | +11,1 |
| 1962-1989 (antes de los índices) | 336 | +10,7 (1,8) | +7,7 (1,3) | +4,7 |

Las dos mitades de 1990-2026 dan lo mismo (+22,9 y +20,3 netos); 76 % de años positivos; todos los meses del
calendario son positivos. El 5 y el 30 años repiten el efecto a escala de su duración (t neto 6,6 y 5,8).
El efecto casi no existía antes de 1990, cuando apenas había gestión indexada: encaja con el mecanismo.

**Secundaria: falla.** Los meses de refinanciación no rinden más: en 1990-2015, +22,0 pb netos frente a +22,5
del resto. Lo que se vio en 2016-2026 con ETF era ruido; se queda la versión de todos los meses.

**Conclusión: pasa.** Es el primer efecto de flujo forzado del proyecto que supera un preregistro con historia
larga, placebo y tramo fuera de muestra. Rinde unos 2,6 % al año sin apalancar sobre el nominal (Sharpe anual neto
0,9) con 36 días invertidos al año, así que pide apalancamiento con futuros. **No es operable en FTMO** (no tiene
bonos) ni pasa el filtro de 40 ops/año del embudo de EAs; su sitio es Darwinex Zero con ZN.

**Límites.** Precio aproximado con rendimientos a plazo constante (el futuro real da algo menos: +14 pb netos).
No se ha hecho el Monte Carlo de Darwinex ni la correlación con el ORB.


## 2026-10-01 · Efecto cambio de mes

**Hipótesis.** Casi toda la rentabilidad del mercado de EE. UU. de 1926 a 2005 se concentró
en la última sesión del mes y las tres primeras del siguiente (McConnell & Xu, 2008). La
pregunta era si sigue ocurriendo después de 2005.

**Regla.** Invertido solo en las `antes` últimas sesiones del mes y las `despues` primeras
del siguiente; el resto del tiempo, en liquidez sin interés. Por defecto 1 y 3, como en el
paper. El walk-forward elige ambos valores (de 1 a 4) por Sharpe en cada ventana de ajuste.

```bash
python -m lab.estrategias cambio-de-mes spy --cost 0.05 --walk-forward
```

**Resultados con 1/3 en toda la muestra.** El coste de 0.05% por lado es realista para SPY
en un bróker barato; 0.15% es el valor por defecto del laboratorio.

| Serie | Periodo | Ret. diario dentro / fuera | t | CAGR (0.05% / ×2) | CAGR comprar y mantener | Sharpe estrategia / B&H |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | 2016-10 a 2026-09 | +0.073% / +0.061% | 0.23 | +2.1% / +0.8% | +15.4% | 0.31 / 0.89 |
| IBEX 35 | 2016-09 a 2026-09 | +0.035% / +0.038% | −0.05 | +0.2% / −1.0% | +8.2% | 0.06 / 0.53 |
| Santander | 2016-09 a 2026-09 | +0.065% / +0.084% | −0.18 | +0.9% / −0.3% | +16.3% | 0.13 / 0.63 |
| BTC | 2017-08 a 2026-10 | +0.291% / +0.130% | 0.98 | +11.0% / +9.7% | +38.5% | 0.58 / 0.83 |

Invertido el 19% del tiempo (13% en BTC, que cotiza todos los días); 121 operaciones en
10 años (111 en BTC).

**Walk-forward (fuera de muestra, 6-7 años).** Con 0.05% y costes al doble: SPY CAGR +6.8% /
+5.5% (Sharpe 0.64 / 0.53), IBEX +4.5% / +3.4%, SAN +7.5% / +6.1%, BTC +2.7% / +1.4%. Mejora
porque el ajuste elige casi siempre la ventana más ancha (4/4), es decir, más tiempo
invertido, no un efecto de calendario. Con 0.15% por lado, SPY baja a +4.1% / +0.2%.

**Conclusión.** En 2016-2026 los días de cambio de mes no rinden más que el resto en SPY,
IBEX ni Santander (t entre −0.18 y 0.23). En BTC la diferencia es mayor, pero no
significativa (t ≈ 1) y el walk-forward no la aprovecha. Como estrategia independiente pierde
claramente frente a comprar y mantener; su única virtud es la menor caída máxima, por estar
fuera del mercado el 80% del tiempo. **Descartada.** Sí tiene sentido como dato: no hay que
esperar un sesgo alcista especial a fin de mes en el US100.

**Límites.** Solo 10 años de datos diarios de Yahoo; no se cobra interés por la liquidez
(que favorecería a la estrategia con tipos altos); no hay series de futuros.

**Pendiente del mismo informe.** El momentum intradía (la primera media hora predice la
última) necesita las velas M1 de US100 del PC de Jorge y el módulo `lab/us100.py` de la
rama `us100-orb-vwap`. Se probará cuando esa rama esté en `main`.

## 2026-11-14 — Revisión de la búsqueda y combinación de indicadores

Informe en `metodo/combinar/INFORME.md`. El ORB v018 real da t 1,15 en 2018-2022: con 5 años el listón lo habría
descartado; las pruebas que deciden deben usar toda la historia. 40 de 79 familias sin bruto: el fallo está en el
origen de las ideas. Meta-etiquetado del ORB con GEX (tamaño por tercil) DESCARTADO: t 2,47 en 2012-2018, nada en
2019-2026.
## 2026-11-14 — Algoritmo desde cero: estudio y gamma de opciones (v5-1)

**Estudio.** Crear desde cero solo tiene opciones partiendo de un flujo forzado medido con un dato nuevo; búsqueda
de patrones, ML sobre precio y microestructura en CFD descartados por el historial (0/28 reglas de precio, atlas sin
supervivientes, LightGBM −0,07 R).

**Prueba preregistrada** (`metodo/v5/PREREGISTRO_GAMMA.md`, subido antes de bajar datos): US500, si la GEX de
SqueezeMetrics del día anterior es negativa, seguir el movimiento 9:30→15:30 en la barra 15:30-15:59, coste 1 pb.
2011-09 → 2026-11, 372 operaciones (25/año): bruto +4,4 pb, neto +3,4 pb, **t 1,11** (listón 2,4), costes ×2 +2,4,
por encima del placebo (p95 +2,1), 2ª mitad +2,4, 2023-26 +2,4. **Cola: caída máxima 60 % a vol 15 % frente a 3×
beneficio anual 12 %.** Réplica US100: +3,7 pb t 1,06, no llega a 1,5. Días de GEX ≥ 0: −0,45 pb bruto.
**NO PASA.** El mecanismo apunta en la dirección correcta, pero los días de gamma negativa son tan volátiles
(σ ≈ 58 pb por media hora) que 25 operaciones al año no dan potencia y la cola es enorme. No se rescata con otros
umbrales (I1 percentil bajo: t 0,5 y 2ª mitad negativa). Corr con el ORB −0,02.
## 2026-11-14 — v7: fuente alternativa (historiales reales de terceros)
- Fuente: supervivientes largos de MQL5 Signals → rejillas en cruces, EAs de oro y scalpers nocturnos. Probada la señal común (reversión nocturna M15, Bollinger 20,2, 18:30-23:00 NY) preregistrada en 9 pares + 4 de réplica, Dukascopy M15 bid/ask 2010-26.
- Bruto real (+0,029 R, t 7,3, por encima del placebo de dirección, nulo a las 08-12) pero ≈ 0,6 pips = la comisión sola. Neto −0,086 R t −23, todos los años negativos; réplica sin bruto. DESCARTADA la familia (scalper y rejilla). metodo/v7/INFORME_V7.md.
## 2026-11-16 — v14: matemática fractal (Hurst DFA) como selector de los ORB
- Preregistro metodo/v14/PREREGISTRO_FRACTALES.md: H por DFA de las 5 sesiones previas y de los 390 min antes de la entrada, régimen persistente = H ≥ mediana de 250 días; bases ORB US100 (réplica 2012-26) y ORB en juego (GER40/UK100/JP225/oro). 4 pruebas.
- US100: persistente +0,23 R vs antipersistente +0,09, coherente en mitades y en v018 real, pero placebo p ≈ 0,05 (p99 no) y Sharpe filtrado < base (0,94-0,98 vs 1,00). En juego: sin efecto o al revés. NINGUNA PASA → DESCARTADO (clase C). metodo/v14/RESULTADOS_V14.md.
- 16-11 (noche, v14b): conmutador por Hurst (sigue si persistente, contra si antipersistente) en GER40/UK100/JP225/oro todos los días 2012-26: neto −0,03 R, pata contra −0,11 R t −4 en los 4 mercados. DESCARTADO (clase A). metodo/v14/RESULTADOS_CONMUTADOR.md.
- 16-11 (v14c): seguimiento en real preregistrado: Hurst H5 de cada día del v018 desde el 17-11; decide con 100 ops (dif persistente − antipersistente > 0, t ≥ 1,65). metodo/v14/seguimiento.py + workflow semanal v14-seguimiento.yml (activo al fusionar).
- 16-11 (v14d): Hurst sobre los descartados prometedores (ORB sin condición GER40/UK100/JP225/oro y gotobi USDJPY con réplicas EURJPY/GBPJPY, M1 2012-26): 0/4 pasan, placebo p 0,39-0,93. Gotobi con bid/ask reales: +0,012 R neto t 0,5. Hurst en M1 no aporta a nada del proyecto; solo queda el seguimiento en real (v14c). metodo/v14/RESULTADOS_DESCARTADOS.md.

## 2026-11-20 — v16: 5 sistemas aleatorios en 5 mercados aleatorios + búsqueda desde los datos
Semilla 20261120 → EURUSD, UK100, JP225, US500, XAUUSD (M5 Dukascopy 2018-26). Los 5 aleatorios y
10.000 más pierden justo el coste; el mejor de 2.000 en 2018-22 pierde fuera. Mapa 2018-22 de 4.628
pruebas con nulo por permutación: 52 celdas |t|≥3 frente a 27,7 del azar (36 en EURUSD).
4 candidatas preregistradas (commit 7f09137) → 0/4 pasan en 2023-26 (mejor: oro largo 06:30 si ayer
cayó, +0,016 R t 1,42). Único patrón persistente: reloj horario EURUSD (Breedon-Ranaldo), 0,26× coste
fuera. DESCARTADO todo. Informe: metodo/v16/INFORME.md.
