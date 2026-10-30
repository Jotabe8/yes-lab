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

## 2026-10-30 · Tendencia con operaciones largas y trailing stop

Ruptura Donchian (20/55/100 días) con stop inicial 3 ATR y trailing chandelier (2/3/4 ATR), largos y
cortos o solo largos, en 39 mercados diarios de Yahoo (índices, forex, metales, energía, agrícolas,
cripto), ajuste 2005-2022, swap con tipos reales de FRED. La principal (55/3/ambos) da +0,031 R bruto,
−0,022 neto y −0,062 con los swaps de FTMO, por debajo del p95 del placebo con las mismas salidas.
La única variante que supera el placebo (100/4/largos) depende de 35 operaciones en cripto; sin cripto,
+0,02 R con swaps de FTMO y −0,17 R a costes ×2; índices −0,16 R con FTMO. **Descartada en P2**
(n_pruebas 27; la prueba 2023-26 no se abrió). Informe: `informes/tendencia_trailing/RESULTADOS.md`.

## 2026-10-30 · Muchas operaciones pequeñas dentro de las normas de FTMO

No se prueba de nuevo: ya lo cubren el scalping con gestión NNFX (105 combinaciones M1-M15, 0 con neto > 0
en 2023-26), la búsqueda de 25.000 reglas intradía y el GER40 EMA20 en 14 mercados. Sin ventaja de entrada,
cambiar stop y objetivo solo reparte el coste; y a menor stop, más pesa el spread. Jorge decide dejarlo descartado.

## 2026-10-30 · Víspera de festivo en índices

Idea no probada antes. 13 índices, ajuste 2000-2022: comprar la víspera de un festivo (apertura → cierre)
da +0,044 R (≈ 0,06 %) frente a −0,005 R de un día normal; supera el placebo y es + en 12/13 índices, pero
el bruto es 1,8× el coste y con costes ×2 pierde. **Descartada en P1** (n_pruebas 3, OOS sin abrir).
Informe: `informes/vispera_festivo/RESULTADOS.md`.

## 2026-10-30 · Ruptura intradía tras día estrecho (NR7, Crabel)

Con índices de contado de Yahoo salía +0,08 R neto (t 9,6) en 18 mercados, pero igual en días normales y sobre
todo en US2000/AUS200: precios rancios del contado. Con futuros (ES, NQ, YM, RTY) el bruto es ≈ 0 y el neto
−0,05 a −0,07 R. **Descartada en P1** (n_pruebas 3, OOS sin abrir). Lección: no probar reglas intradía con
máximos/mínimos/apertura de índices de contado de Yahoo. Informe: `informes/nr7/RESULTADOS.md`.

## 2026-10-30 · Tendencia en cuenta sin swap

Sin financiación, la tendencia 100/4 (contado: índices, forex, metales) gana en ajuste (+0,16 R, t 3,4) pero en
2023-26 (abierto una vez) da +0,12 R por debajo del placebo de largos al azar (+0,19); largos y cortos −0,07 R.
Es deriva, no tendencia. **Descartada.** Lo que queda útil: la cesta larga (IndexBasket) en una cuenta sin swap
(E8PRO v2, FTMO o The5ers bajo petición). Informe: `informes/tendencia_trailing/SIN_SWAP.md`.

## 2026-10-30 · Cesta de índices sin swap con reglas de E8 Pro

Normas verificadas (help center E8, tradetanto ago-2026): 1 fase 8 %, diario 2,5 %, máx 8 % estática (al saldo
inicial tras el 1er retiro), tope 2 %/día, retiros diarios del 50 %, una estrategia por usuario; swap en índices
sin confirmar. Monte Carlo 3 años (6 índices, SMA200, vol 5-10 %): cobro medio 1.100-1.300 $ por cuenta de 100K
esperando al 4-8 % para el primer retiro (control 500-600 $), mediana 0 $. No compensa ocupar la plaza de E8
(mejor el ORB). Pendiente: preguntar a FTMO por swap-free en índices. Informe: `informes/cesta_sin_swap/`.

## 2026-10-30 · Buscar un sistema distinto al ORB: periodicidad intradía y deriva EIA

Dos ideas nuevas preregistradas. **Periodicidad intradía** (ir en la dirección de la misma media hora de
los 20 días anteriores o de las 8 semanas anteriores, 10 mercados, 2018-22): bruto −0,29/−0,15 pb frente
a 2 pb de coste, 0/20 sobre el placebo. **Descartada en P1.** **Deriva tras el inventario de crudo EIA**
(USOIL, dirección de 10:30-10:35 NY, salida 14:30): ajuste 2021-22 +33 pb (t 2,1) con meseta, pero
2023-26 +11 pb (t 1,1, bajo el p95 del placebo) y neto con stop 0,5 ATR +0,02 R (t 0,37), negativo en 2026.
**Descartada en P3** (n_pruebas 41). Informe: `informes/distinta_orb/RESULTADOS.md`.
