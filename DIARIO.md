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
| 2026-10-25 | Momentum intradía al cierre y zona de ruido (Zarattini) | US100.cash M1 FTMO | Descartado el momentum de cierre y la extensión del ORB; zona de ruido en reserva (no mejora frente a subir el riesgo del ORB) |
| 2026-10-25 | Efecto Halloween | SPY, IBEX, SAN + 10 índices D1 | No pasa: falla en EE. UU. y Japón; en Europa y Hong Kong sí aparece |
| 2026-10-25 | Oro largo en sesión asiática | XAUUSD M1 | Descartada: neto negativo dentro de muestra |
| 2026-10-25 | Prima nocturna EE. UU. | US500, US100 M1 | Descartada: el swap y el spread se comen el efecto |
| 2026-10-25 | Fin de mes en forex (Melvin y Prins) | EURUSD, GBPUSD, AUDUSD, USDJPY | Descartada: sin efecto |
| 2026-10-25 | Momentum intradía BTC | BTCUSDT 30m | Descartada: negativa incluso sin costes |
| 2026-10-25 | Valor relativo (11 pares D1) | Índices, forex, metales, petróleo | Descartada: sin edge ni antes de costes |
| 2026-10-01 | Cambio de mes | SPY, IBEX, SAN, BTC | Descartada: sin efecto medible en 2016-2026 |

---

## 2026-10-25 · Momentum intradía al cierre en US100 (complemento del ORB)

Reglas fijadas antes en `informes/momentum-cierre-preregistro.md`; detalle en
`informes/momentum-cierre-resultados.md`. US100.cash M1 de FTMO 2021-10 a 2026-09 (1.228 días),
Dukascopy 2018-2021 aparte. La regla básica ya se había probado el 24/10 en el PC (≈0 neto); aquí
se completa el resto del informe.

```bash
python -m lab.momentum_cierre todo --m1 datos/US100_cash_M1_FTMO.csv --orb datos/orb_R_2018_2026.csv
```

| Prueba | Costes ×1 | Costes ×2 | Fuera de muestra (×2) |
| --- | --- | --- | --- |
| Regresión 22:30-23:00 sobre el día | pendiente 0,006 (t 0,6), R² 0,07 % | | |
| Complementaria 22:30-22:55 | −0,029 R/op | −0,055 R | −0,13 y −0,00 |
| Extensión del ORB a 22:55 | −0,006 R/op del ORB | −0,006 R | peor en las dos |
| Zona de ruido (Zarattini, sin ajustar) | +0,119 R/día (t 2,3) | +0,096 (t 1,9) | +0,082 y +0,053 (t 0,8 juntas) |

Spread real de 22:30 a 23:00: 0,8-0,9 puntos (2,2 desde las 23:01); el coste no es el problema,
el efecto no existe en el CFD desde 2023. La zona de ruido cumple el listón por la mínima, pero se
apaga (2025 +0,07, 2026 +0,02 R/día), pierde hasta −7 R en un día y en EV por cuota (2-Step 100K)
el ORB más la zona de ruido a medio tamaño da +24.000 €/año con costes al doble frente a +26.400 €
de subir el riesgo del ORB un 25 %. **Veredicto:** momentum de cierre y extensión descartados;
zona de ruido en reserva, no se escribe en MQL5.

---

## 2026-10-25 · Efecto Halloween ("Sell in May")

**Diseño contra el sobreajuste** (fijado antes en `informes/halloween-preregistro.md`): la regla
del artículo sin ningún parámetro (invertido de noviembre a abril), la diferencia invierno −
verano medida año a año, 13 mercados en una lista cerrada, un placebo con los 12 semestres
posibles y los años posteriores a 2017 como fuera de muestra del artículo.

```bash
python -m lab.estrategias halloween
```

**Resultados.** 148 mercado-años (2012-2024): invierno − verano = +4,1 puntos de media (t 2,8).
Después de 2017: +4,3 puntos (t 2,0). Noviembre-abril es el mejor de los 12 semestres del
placebo. Pero el efecto es regional:

| Mercados | Media invierno − verano |
| --- | --- |
| IBEX, Santander, GER40, FRA40, EU50, UK100, Hang Seng, ASX | de +2,7 a +20 puntos |
| SPY, US500, US100, US30, Nikkei | de −6,2 a −0,1 puntos |

Como estrategia, con liquidez sin interés: SPY Sharpe 0,52 frente a 0,89 de comprar y mantener
(CAGR +6,8 % frente a +15,4 %); IBEX 0,55 frente a 0,53; Santander 0,65 frente a 0,63, con
caídas máximas menores en los dos españoles.

**Veredicto: no pasa.** Cumple dos de las cuatro condiciones (media global con t > 2 y primer
puesto en el placebo), pero falla en la amplitud (8 de 13 mercados positivos, hacía falta 9) y en
SPY como estrategia. El t global exagera, porque las bolsas se mueven juntas y 10-12 años por
mercado son pocos. Quedarse solo con Europa sería elegir a posteriori. Como dato, en bolsas
europeas el verano ha sido peor que el invierno 8-9 de cada 12 años.

---

## 2026-10-25 · Segunda ronda: fin de mes en forex, prima nocturna y oro en Asia

Reglas fijadas antes en `informes/ronda2-preregistro.md`; detalle en `informes/ronda2-resultados.md`.
Las tres fallan. Antes de costes hay efecto en la prima nocturna (+0,04 % por noche en US500) y en
el oro asiático (+0,07 % fuera de muestra), pero el spread y el swap de un CFD cuestan lo mismo.
El fin de mes en forex no muestra efecto ni antes de costes.

---

## 2026-10-25 · Momentum intradía en Bitcoin

Reglas fijadas antes de descargar los datos en `informes/btc-intradia-preregistro.md`
(Shen, Urquhart y Wang, 2022). Velas de 30 min de BTCUSDT en Binance, 2017-08 a 2026-10
(3.353 días), descargadas con el workflow `descargar-intradia.yml`.

| Regla | Coste | Dentro (hasta 2020) | Fuera (2021-2026) |
| --- | --- | --- | --- |
| Signo de 00:00-00:30 → 23:30-24:00 | 0 | −0,027 % (t −1,5) | −0,009 % (t −1,1) |
| Ídem | 0,05 % | −0,077 % (t −4,1) | −0,059 % (t −7,0) |
| Signo de r1 + 23:00-23:30 | 0 | −0,018 % (t −1,0) | +0,000 % (t 0,0) |
| Ídem | 0,05 % | −0,068 % (t −3,7) | −0,050 % (t −5,9) |

Negativa en todos los años con costes. **Descartada**: el efecto no aparece ni antes de costes
en Binance, y con el spread de un CFD pierde con claridad.

---

## 2026-10-25 · Valor relativo entre mercados parecidos (pares)

Reglas fijadas antes en `informes/pares-preregistro.md`; detalle en `informes/pares-resultados.md`.
11 pares (US500 contra US100, US30 y US2000; GER40, FRA40 y UK100 contra EU50; GER40/FRA40;
oro/plata; EURUSD/GBPUSD; AUDUSD/NZDUSD; Brent/WTI) con datos D1 de Dukascopy 2010-2025.
Entrada con |z| > 2 del diferencial, salida en |z| < 0,5, |z| > 4 o 20 días.

Fuera de muestra (2020-2025), todos los pares juntos: −1,0 % por operación con costes (t −4,9),
−0,08 % sin costes. Solo 2 de 11 pares positivos. **Descartada.** La financiación de las dos
patas del CFD se come cerca del 1 % por operación, y antes de costes tampoco hay efecto.

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
