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
| 2026-11-14 | Revisión 2 de descartados con el motor nuevo (paseo aleatorio en gotobi, EIA, ORB GER40, ORB JP225 y subastas; auditoría de código de las clases B y D) | varios | **Ninguna revive**: motores limpios (sesgo ≈ 0, ninguno negativo); la única regla pesimista (ORB acciones) no pudo esconder ventaja. `metodo/revision2/` |
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
