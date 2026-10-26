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

## 2026-10-26 — Cuatro ideas por el embudo: las cuatro descartadas

Primera tanda con el método del embudo (`metodo/METODO.md`), preregistro antes de mirar datos
en cada una. Datos: M1 bid/ask de Dukascopy y de FTMO del PC de Jorge.

| Idea | Mercados | Dónde cae |
| --- | --- | --- |
| Gotobi (días de liquidación japoneses, compra de USDJPY en la fijación de Tokio) | USDJPY, EURJPY, GBPJPY | P1/P2: el efecto es real (+0,106 R bruto, t 3,5; se repite en los tres cruces) pero son 2,4 pips contra 1,6 de coste; bruto 1,5× coste y neto ×2 de −0,037 R |
| Continuación del shock macro de las 08:30 de Nueva York | XAUUSD, US500, US30, US2000, EURUSD | P1: bruto +0,016 R = 0,5× coste y por debajo del p95 del placebo |
| Asia marca el día en Europa (JP225 + HK50 → apertura europea) | FRA40, EU50, UK100 | P1-P3: neto −0,047 R dentro y −0,057 fuera de muestra |
| Prima nocturna tras un día de estrés (caída de sesión > 1,5 %, comprar al cierre, vender en la apertura siguiente) | US500, US30, US2000, FRA40, EU50, UK100, GER40 | P1: bruto real −0,086 R (t −1,9) |

La prima nocturna pareció pasar todas las puertas (+0,183 R brutos, EV 2-Step +5.139 €) y se
llegó a escribir el EA, pero era un fallo del backtest: la R se calculaba como
`max((salida − entrada) / stop, −1)`, un stop que corta los huecos a −1 R y nunca salta en las
caídas nocturnas que se recuperan. Recorriendo las velas M1 de toda la noche (stop en la primera
vela que lo toca, huecos llenados a la apertura) sale −0,086 R bruto y −0,112 neto, negativo en
los siete mercados y en los dos periodos. Sin stop, +0,005 R, por debajo de las noches normales.
EA retirado. Detalle en `cartera/noche_estres/RESULTADOS_NOCHE.md`.

**Lección para el método:** toda salida por stop se comprueba vela a vela entre entrada y salida,
y los huecos se llenan a la apertura. Recortar el resultado final a −1 R es mirar el futuro.
