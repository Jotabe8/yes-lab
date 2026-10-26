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

## 2026-10-26 · Entrada aleatoria con gestión NNFX (descartada)

Moneda (largo/corto al 50 %) con cinco gestiones NNFX fijadas de antemano (1:1, VP con mitad a 1 ATR + BE +
trailing 2 ATR, TP 1 ATR, Van Tharp trailing 3 ATR, VP con cierre a 20 días) en 24 mercados D1, 2018-2026,
100 semillas, spread y financiación. Bruto ≈ 0 en todas (|t| < 2); neto −0,03 a −0,09 R por operación en
ajuste y prueba. EV por cuota FTMO negativo salvo +55 € en 2-Step 100K midiendo solo al cierre, que se vuelve
negativo al doble de costes. El control de media cero da +1.569 €: la estructura de FTMO no basta para cubrir
el coste de 600-1.400 operaciones al año. **Descartada.** Detalle en `informes/entrada_aleatoria/RESULTADOS.md`.

## 2026-10-26 · Scalping con gestión NNFX (descartado)

Velas M1 bid/ask en 7 mercados (EURUSD, GBPUSD, USDJPY, oro, US100, US500, GER40), M1/M5/M15, solo en sesión
líquida, gestión NNFX (SL 1,5 ATR, mitad a 1 ATR, BE, trailing 2 ATR) y cuatro entradas pre-registradas
(aleatoria, retroceso a EMA20, ruptura Donchian 20, RSI(2) a favor de la EMA200). 0 de 105 casillas ganan en
2023-26. El spread cuesta 0,3-0,4 R por operación en M1 en forex y oro y 0,02-0,03 R en índices FTMO en M15; el
bruto no lo cubre en ningún caso. La única casilla con t > 2 en ajuste (ruptura US100 M15, +0,078 R) da −0,006 R
en prueba. **Descartado.** Detalle en `informes/scalping_nnfx/RESULTADOS.md`.

## 2026-10-26 · Scalping de coste bajo: indicio en GER40 (pendiente de Strategy Tester)

US100 y GER40, M15/M30, señal solo en la primera hora y media de contado, máximo 2 operaciones al día, filtro de
coste y dos gestiones NNFX. Coste de 0,015 a 0,05 R. De 48 casillas pasa una, GER40 M30 con retroceso a EMA20 y
corredor: +0,060 R en ajuste (t 0,95) y +0,191 R en prueba (t 2,13), 8 de 9 años positivos, EV +4.779 € en 2-Step
100K (control +1.435 €). Aviso: con dirección aleatoria en las mismas velas sale +0,096 R en prueba, así que gran
parte es momento de entrada más corredor. Detalle en `informes/scalping_nnfx/RESULTADOS_COSTE_BAJO.md`.
