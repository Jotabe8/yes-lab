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
