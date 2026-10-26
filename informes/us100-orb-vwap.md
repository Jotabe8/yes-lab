# ORB y VWAP en US100 en el laboratorio

Prueba simulada, sin dinero real, de los dos EAs del proyecto *Prop Firm Challenges*
(septiembre de 2026). Nada de esto es una recomendación de inversión.

## Qué se ha portado

`lab/us100.py` reproduce la configuración por defecto de los dos EAs, sin dependencias:

| EA | Señal | Stop y salida | Riesgo |
| --- | --- | --- | --- |
| ORB_US100 v0.16 | Dirección de la vela de los primeros 10 min desde las 16:30 del servidor (no opera si el cuerpo es < 10% del rango ni en festivos USA) | Stop 15% del ATR(14) diario, sin objetivo, cierre a las 22:30 | 0.5% del tamaño nominal, tope de exposición 6× |
| VWAPMeanReversion_US100 v0.20 | M5: cierre fuera de VWAP ± 1.5σ, ADX(14) < 30 y vela de giro; de 16:40 a 22:00 | Stop 1.5×ATR(14) M5, objetivo el VWAP (B/R ≥ 0.5), salida a las 24 velas o a las 22:45 | 0.5%, 3 operaciones y +2% al día como máximo |

Costes: el spread registrado en la vela de entrada (mediana 1 punto a las 16:40) más
0.2 puntos de deslizamiento por operación, sin comisión. "Costes al doble" duplica todo.

**Datos.** El máximo histórico intradía del PC son las velas M1 de US100.cash en FTMO-Demo:
del 14-09-2021 al 30-09-2026 (1.279 sesiones). Antes de esa fecha el servidor solo guarda
velas diarias. Los ticks empiezan en febrero de 2022, así que no añaden años. Los datos no
están en el repo; `python -m lab.us100 --export` los vuelca desde MetaTrader 5.

El servidor sigue el horario de verano de EE. UU. (la vela de mayor rango en las semanas de
desfase de marzo es la de las 16:30), así que la hora fija del EA cae siempre en la apertura.

## Paridad con el tester de MT5

Con el CSV del propio EA (`ORB_backtest_v16.csv`: US100.nocom, enero a septiembre de 2026,
cuenta de 10.000 al 0.5%), el port abre **las mismas 171 operaciones**, el mismo día y en el
mismo sentido. 170 terminan igual (stop o cierre a las 22:30) y la diferencia mediana en R es
0.055, que viene del spread y el deslizamiento. El VWAP no tiene un backtest previo en US100
con el que compararlo (el CSV que hay es de EURUSD), así que su port no está verificado
contra el tester.

## Comprobación del riesgo

A diferencia del motor Python del NNFX, aquí el riesgo es el configurado:

- Con 0.5%, el riesgo de cada operación es entre el 99.7% y el 100% del configurado (el
  resto es el redondeo del lote a 0.01). El tope de 6× no actúa nunca.
- Las operaciones que tocan el stop pierden de media −1.005 R; la peor, −1.48 R (hueco).
- Con 2% y el tope por defecto de 6×, el tope recorta 778 de 1.153 operaciones (riesgo
  mediano real 1.6%). La versión AGR v0.17 sube el tope a 20× y no tiene ese problema.

## Resultados (capital 100.000, riesgo 0.5%)

| Periodo | Costes | Total | CAGR | Caída máx | Sharpe | PF | Operaciones | R medio (t) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORB 2021-09 a 2026-09 | normales | +106.9% | +15.1% | −12.0% | 1.23 | 1.26 | 1.153 | +0.186 (2.8) |
| ORB 2021-09 a 2026-09 | al doble | +92.3% | +13.5% | −12.2% | 1.07 | 1.22 | 1.153 | +0.160 (2.4) |
| ORB 2021-09 a 2023-12 | normales | +38.1% | +14.7% | −12.0% | 1.05 | 1.20 | 521 | +0.146 (1.5) |
| ORB 2021-09 a 2023-12 | al doble | +28.3% | +11.2% | −12.2% | 0.80 | 1.15 | 521 | +0.109 (1.1) |
| ORB 2024-01 a 2026-09 | normales | +64.4% | +19.3% | −10.8% | 1.43 | 1.31 | 632 | +0.218 (2.4) |
| ORB 2024-01 a 2026-09 | al doble | +59.8% | +18.1% | −11.2% | 1.34 | 1.29 | 632 | +0.203 (2.2) |
| VWAP 2021-09 a 2026-09 | normales | −28.7% | −6.3% | −35.7% | −0.79 | 0.84 | 681 | −0.084 (−2.1) |
| VWAP 2021-09 a 2026-09 | al doble | −40.5% | −9.5% | −46.3% | −1.12 | 0.78 | 680 | −0.119 (−3.0) |
| Comprar y mantener US100 | | +98.2% | +14.1% | −35.6% | 0.70 | | | |

ORB por años (costes normales): PF 1.49 en 2021 (desde septiembre), 1.14 en 2022, 1.20 en
2023, 1.54 en 2024, 1.14 en 2025 y 1.25 en 2026. Todos los años ganan, incluido el bajista
2022. Largos y cortos aportan parecido (+0.16 R y +0.21 R). El 70% de las operaciones acaba
en stop; el beneficio viene del 30% que llega a las 22:30.

VWAP pierde todos los años salvo 2025 (PF 1.08) y 2026 (PF 1.00).

**Comparación con los resultados previos.** El backtest del 27-09-2026 del proyecto daba 628
operaciones, R medio +0.23, t = 2.5 y PF 1.55 en 2024. El port, en el mismo periodo
(2024-01 a 2026-09), da 632 operaciones, +0.218, t = 2.4 y PF 1.54 en 2024. Los 27 meses
anteriores, que no se usaron para elegir la configuración, siguen siendo positivos pero más
flojos: R medio +0.146 (+0.109 con costes al doble) y t = 1.5, que por sí solo no sería
significativo.

## Walk-forward

Mismo método que el NNFX: elige parámetros por Sharpe en 3 años y los mide en el año
siguiente. Rejilla: rango de 5, 10, 15 o 30 minutos y stop del 10, 15, 20 o 30% del ATR.
Con datos desde septiembre de 2021 solo caben dos ventanas.

| Ventana fuera de muestra | Elegido | Fija (10 min, 15%) | Reoptimizada |
| --- | --- | --- | --- |
| 2024-09 a 2025-09 | 15 min, 30% | +5.2% | +10.3% |
| 2025-09 a 2026-09 | 15 min, 30% | +21.4% | −0.8% |
| Encadenado, costes normales | | +28.0% (caída −14.3%) | +9.7% (caída −8.3%) |
| Encadenado, costes al doble | | +23.8% (caída −14.8%) | +7.0% (caída −8.8%) |

Las dos ventanas de la configuración fija son positivas. Reoptimizar no mejora el resultado.
Con dos ventanas, esto es una comprobación débil. VWAP: fija −1.9% (−6.2% al doble),
reoptimizada +1.2% (−0.1% al doble).

## Monte Carlo del challenge FTMO

Mismas reglas que en el NNFX: bootstrap de días reales (los días sin operación cuentan como
0), 5.000 trayectorias de hasta 500 días, objetivo +10%, caída diaria 5% y caída total 10%
medida desde el máximo.

| Estrategia | Días que se remuestrean | Riesgo | Costes | P(pass) | P(fail) | Mediana hasta pasar | Caída P95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORB | 2021-09 a 2026-09 | 0.5% | normales | 80.7% | 18.9% | 102 días | 10.2% |
| ORB | 2021-09 a 2026-09 | 0.5% | al doble | 74.8% | 25.0% | 98 días | 10.3% |
| ORB | 2021-09 a 2023-12 | 0.5% | normales | 70.8% | 29.2% | 77 días | 10.3% |
| ORB | 2021-09 a 2023-12 | 0.5% | al doble | 63.2% | 36.8% | 74 días | 10.4% |
| ORB | 2024-01 a 2026-09 | 0.5% | normales | 85.7% | 14.2% | 89 días | 10.2% |
| ORB | 2021-09 a 2026-09 | 0.4% | normales | 84.7% | 13.7% | 133 días | 10.2% |
| ORB AGR (tope 20×) | 2021-09 a 2026-09 | 2% | normales | 58.4% | 41.6% | 21 días | 11.0% |
| ORB AGR (tope 20×) | 2021-09 a 2026-09 | 2% | al doble | 54.6% | 45.4% | 18 días | 11.0% |
| VWAP | 2021-09 a 2026-09 | 0.5% | normales | 8.4% | 85.9% | 206 días | 11.0% |
| VWAP | 2021-09 a 2026-09 | 0.5% | al doble | 5.2% | 93.1% | 161 días | 11.1% |

Las dos fases seguidas (+10% y después +5%, cada una con las mismas reglas): ORB al 0.5%
pasa el 72.8% (64.2% con costes al doble), con una mediana de 172 días en total; AGR al 2%,
el 41.9%, con una mediana de 37 días.

El bootstrap mezcla días sueltos y pierde las rachas. Como contraste, empezar el challenge en
cada uno de los 1.055 días reales posibles y seguir la historia tal cual: ORB al 0.5% pasa el
90.5% de las veces y falla el 6.7% (88.7% y 8.5% con costes al doble); AGR al 2% pasa el
66.9% y falla el 33.1%.

## Cosas del EA que conviene revisar

1. **El cierre antes del FOMC no funciona.** `NewsExitCheck` sale en la primera línea si
   `InpNewsExit` es falso (`ORB_US100_v016.mq5`, línea 502), así que `InpFomcClose = true`
   no hace nada aunque el mensaje de la build diga que está activo. El backtest (el del
   tester y este) tampoco cierra antes del FOMC.
2. **La lista de festivos acaba en 2026.** Hay que añadir los de 2027 antes de enero.
3. **Comisión.** El tester ignora la comisión y este port supone 0 en índices de FTMO. La
   primera operación en demo debe confirmarlo; `analizar_forward.py` ya lo informa.

## Conclusión

Al revés que el NNFX, el ORB conserva la ventaja fuera del periodo con el que se eligió: los
27 meses previos a 2024 ganan en todos los años, con costes al doble y en las dos ventanas del
walk-forward con la configuración fija. La ventaja es menor fuera de muestra (+0.15 R frente a
+0.22 R por operación), y con cinco años de datos intradía la evidencia es moderada, no
concluyente. Con el riesgo del EA (0.5%) y las reglas del Monte Carlo del NNFX, la
probabilidad de pasar la fase 1 queda entre el 63% y el 81% según los días y los costes, y la
de pasar las dos fases, en torno al 64–73%. La versión agresiva al 2% pasa antes pero falla
cuatro de cada diez intentos. El VWAP no tiene ventaja: pierde con costes normales en casi
todos los años.
