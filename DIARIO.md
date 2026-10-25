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
| 2026-10-25 | Rebalanceo de fin de mes (60/40) | SPY con TLT | Prometedora pero frágil: el efecto aparece, el walk-forward es inestable |
| 2026-10-25 | Volatilidad gestionada | SPY, IBEX, SAN, BTC, ETH | Sin ventaja en Sharpe fuera de muestra; solo reduce caídas |
| 2026-10-25 | Momentum de divisas | 6 divisas G10 frente al USD | Descartada: pierde con todos los horizontes |
| 2026-10-01 | Cambio de mes | SPY, IBEX, SAN, BTC | Descartada: sin efecto medible en 2016-2026 |

---

## 2026-10-25 · Rebalanceo de fin de mes

**Hipótesis.** Los fondos mixtos (pensiones, 60/40) rebalancean de forma predecible. Cuando
las acciones han subido más que los bonos, a fin de mes venden acciones y compran bonos, y al
revés. Harvey, Mazzoleni & Melone (2025) estiman una caída de 17 pb en las acciones al día
siguiente cuando están sobreponderadas. Es una ventaja de **flujos**, no una anomalía de
calendario: tiene un motivo económico y alguien que paga por ella (unos 16.000 millones de
dólares al año, según el paper).

**Regla.** Cuando quedan `dias` sesiones para fin de mes, calcula el peso de las acciones en
una cartera 60/40 (SPY/TLT) rebalanceada al cierre del mes anterior. Si pasa del 60% más el
umbral, vende SPY hasta el último cierre del mes; si queda por debajo, lo compra. El resto
del mes, en liquidez. Añade la serie TLT a `lab/fetch.py`.

```bash
python -m lab.estrategias rebalanceo spy --bonos tlt --dias 1 --cost 0.05
```

**Resultados 2016-10 a 2026-10, sin umbral, 0.05% por lado.**

| Ventana | Rentabilidad media de SPY en días cortos (t) | En días largos (t) | CAGR | Caída máx | Sharpe |
| --- | --- | --- | --- | --- | --- |
| Última sesión | −0.184% (−2.02), 77 días | +0.286% (1.65), 43 días | +1.4% | −6.2% | 0.45 |
| 2 últimas | −0.038% (−0.55) | +0.287% (2.29) | +1.9% | −9.2% | 0.41 |
| 5 últimas | +0.004% (0.09) | +0.211% (2.74) | +3.0% | −11.6% | 0.41 |

La media de SPY en un día cualquiera es +0.063%. El último día del mes tras sobreponderación
cae −0.18%, el mismo orden que los 17 pb del paper, y fuera de la muestra de este.

Solo con SPY (sin bonos, usando la subida del mes como señal) no funciona: walk-forward
−1.1% anual. Hace falta la comparación con los bonos.

**Walk-forward (6 años).** Sharpe 0.25 con 0.05% y 0.01 con costes al doble; con 0.02%,
0.07. El resultado depende de qué ventana elija cada año, y el ajuste salta entre 3 y
5 días: es inestable.

**Conclusión.** **Prometedora, pero frágil.** El efecto del último día aparece en estos
10 años con el signo y el tamaño del paper. Pero la ganancia es pequeña (está invertido
solo un 5% del tiempo) y la elección de la ventana no es estable. Como estrategia
independiente no compensa; como **filtro** puede servir, por ejemplo para no abrir largos en
US500/US100 el último día de un mes en que la bolsa ha batido mucho a los bonos. Siguiente
paso: probarla con futuros o CFD en MT5 (coste menor) y con la cartera de bonos agregada (AGG).

**Límites.** TLT es un bono largo, más volátil que la cartera de bonos de un fondo real; sin
interés por la liquidez; solo 120 meses.

---

## 2026-10-25 · Volatilidad gestionada

**Hipótesis.** Reducir la exposición cuando la volatilidad reciente es alta y subirla cuando
es baja mejora el Sharpe, porque la volatilidad persiste y el retorno esperado no sube con
ella (Moreira & Muir, 2017: alfa del 4,86% anual en el mercado de EE. UU. de 1926 a 2015).
Cederburg et al. (2020) lo repiten en 103 estrategias y concluyen que, aplicado en tiempo
real, no supera en general a la cartera sin gestionar.

**Regla.** A fin de mes, exposición = objetivo / volatilidad anualizada de los últimos
21 días, con un tope de 1 (sin apalancamiento). El walk-forward elige el objetivo (8-30%) y
la ventana (21 o 63 días) por Sharpe.

```bash
python -m lab.estrategias vol-gestionada spy --cost 0.05 --walk-forward
```

**Resultados, coste del 0.05% por lado** (los costes al doble apenas cambian nada: unos
12 reajustes pequeños al año).

| Serie | Fijo 12%/21 días: CAGR, caída, Sharpe | B&H: CAGR, caída, Sharpe | Walk-forward: Sharpe | B&H mismos años: Sharpe |
| --- | --- | --- | --- | --- |
| SPY | +11.6%, −23.0%, 0.95 | +15.4%, −33.7%, 0.89 | 0.78 | 0.85 |
| IBEX 35 | +6.0%, −34.1%, 0.51 | +8.2%, −45.2%, 0.53 | 0.68 | 0.69 |
| Santander | +7.1%, −40.3%, 0.57 | +16.3%, −72.1%, 0.63 | 0.78 | 0.78 |
| BTC | +11.8%, −27.1%, 0.83 | +38.5%, −83.2%, 0.83 | 0.49 | 0.77 |
| ETH | +10.3%, −25.8%, 0.77 | +27.1%, −94.0%, 0.71 | 0.28 | 0.70 |

Con tope de 1.5 (algo de apalancamiento) en SPY, el walk-forward da un Sharpe de 0.90
frente a 0.85, con CAGR +18.7% frente a +16.7% y la misma caída máxima: una mejora pequeña
que no es significativa con 6 años.

**Conclusión.** Fuera de muestra no mejora el Sharpe en ningún mercado; en cripto lo
empeora bastante. Lo que sí hace siempre es recortar la caída máxima (de −83% a −27% en BTC
con parámetros fijos) a cambio de menos rentabilidad. **No es una fuente de ventaja**, pero
sí una regla útil de gestión del tamaño de la posición, por ejemplo para limitar la caída en
un challenge.

**Límites.** 10 años; sin interés por la liquidez; SPY de 2016 a 2026 apenas tuvo
caídas largas, que es donde la regla más ayuda.

---

## 2026-10-25 · Momentum de divisas

**Hipótesis.** Las divisas que más se han apreciado en los últimos meses siguen haciéndolo:
diferencial de hasta el 10% anual entre ganadoras y perdedoras (Menkhoff, Sarno, Schmeling
& Schrimpf, 2012), concentrado en divisas caras de operar y con fuertes límites al arbitraje.

**Regla.** Seis divisas frente al dólar (EUR, GBP, AUD, NZD, JPY, CHF), construidas a partir
de los 7 pares del laboratorio con el cierre corregido de Yahoo. A fin de mes compra las 2 que
más han subido en N meses y vende las 2 que menos (exposición bruta 1). Coste del 0.02% por
lado sobre lo que cambia. Solo precio, sin el diferencial de tipos.

```bash
python -m lab.estrategias momentum-divisas fx --cost 0.02 --walk-forward
```

**Resultados 2016-2026.** CAGR −1.4% (1 mes), −2.2% (3 meses), −1.4% (6 meses) y
−0.7% (12 meses); Sharpe entre −0.18 y −0.60. Walk-forward (7 años): −1.1% anual, Sharpe
−0.27; con 1 larga y 1 corta, −1.2%. Los costes no son el problema: el resultado es
negativo antes de costes.

**Conclusión.** **Descartada** en divisas principales. Coincide con el paper: el efecto vive
sobre todo en divisas emergentes poco líquidas, a las que un minorista apenas accede.

**Límites.** Solo 6 divisas (dos posiciones por lado, mucho ruido) y sin carry; con swaps,
el resultado cambiaría según el diferencial de tipos de cada año.

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
