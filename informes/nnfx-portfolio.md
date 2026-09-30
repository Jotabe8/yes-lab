# Portfolio NNFX de 5 pares en el laboratorio

Prueba simulada, sin dinero real, del sistema NNFX validado para el FTMO Challenge
(proyecto *NNFX algo FTMO challenge*, configuración cerrada el 2026-05-10). Nada de esto es
una recomendación de inversión.

## Qué se ha portado

`lab/nnfx.py` reproduce `nnfx_clasico_v1` (indicators.py + backtest.py) sin pandas:

| Par | Baseline | C1 | C2 | Volumen |
| --- | --- | --- | --- | --- |
| NZDUSD, USDCHF, USDJPY, GBPJPY | ALMA(50, σ 6, offset 0.85) | ASH(9, 2) | SSL(10) | vela no blanca |
| EURAUD | Kijun(26) | ASH(9, 2) | SSL(10) | vela no blanca |

Entrada en la apertura siguiente a la señal, regla de 7 velas, regla de una vela y
"bridge too far" de 1 ATR. Posición única con SL 1×ATR y TP 1.5×ATR, salida al cierre si
ASH o SSL se giran o el precio cruza la baseline. Riesgo 0.40% por operación. Costes de
`costs.py` (spread en pips + 7 USD por lote); "costes al doble" duplica spread y comisión.

**Paridad.** Con los mismos datos Dukascopy desde 2020, el port reproduce el motor original
operación a operación en NZDUSD, USDJPY, EURAUD y GBPJPY. En USDCHF difiere desde septiembre
de 2020 por un empate numérico (el ASH vale exactamente 0 y pandas lo redondea a −2e‑18).

## Hallazgo 1: el motor Python arriesgaba el doble

En modo posición única, `backtest.py` calcula los lotes para el riesgo completo y luego los
aplica a las dos "mitades" (#1 y runner). Un stop pierde ~0.8% con `risk_pct_per_trade=0.4`.
El EA MQL5 arriesga lo configurado. Por tanto, el Monte Carlo de 69.7% P(pass) y el DD P95
de 10.5% se calcularon con un riesgo efectivo de 0.8%, no de 0.4%. El port usa el riesgo real
y tiene un test que lo comprueba.

## Hallazgo 2: los datos de forex de Yahoo necesitan rehacerse

Yahoo pone como cierre diario de forex el precio del arranque de la sesión, casi igual a la
apertura. Con esas velas solo el 2% cumple la regla de volumen y el sistema apenas opera.
`nnfx.daily_bars` usa como cierre la apertura de la vela siguiente; así el 40–45% de las
velas tienen convicción, igual que con Dukascopy, y el número de operaciones casa (80–100 por
par desde 2020 en ambas fuentes).

## Resultados (riesgo real 0.40%, capital 100.000)

Datos Yahoo, 2016-09 a 2026-09 (`python -m lab.nnfx --walk-forward`):

| | Total | CAGR | Caída máx | Sharpe |
| --- | --- | --- | --- | --- |
| NNFX, costes normales | −3.5% | −0.3% | −14.8% | −0.07 |
| NNFX, costes al doble | −8.6% | −0.9% | −17.8% | −0.20 |
| Comprar y mantener (cesta de los 5 pares) | +87.2% | +6.3% | −23.7% | 0.46 |

Solo 2020-01 a 2026-09 (`--since 2020-01-01`): +5.6% con costes normales y +2.9% al doble
(Sharpe 0.24 y 0.13), frente a +60.5% de la cesta. EURAUD aporta casi todo; los otros cuatro
pares quedan entre −1.7% y +1.0% según los costes.

Walk-forward (3 años de entrenamiento, 1 año fuera de muestra, 6 ventanas por par, costes al
doble): configuración fija +6.5% total, CAGR +1.0%, caída −8.1%, Sharpe 0.31; reoptimizando
baseline y SSL cada año, +6.7%. Ventanas positivas por par con la configuración fija: 2 a 4
de 6.

Comprar y mantener no es comparable en riesgo: es una exposición del 100% sin apalancamiento
y su resultado viene sobre todo de la caída del yen. El Sharpe es la comparación más justa.

### Contraste con datos Dukascopy de 2005 a 2019

La configuración se eligió con datos desde 2020. Con el histórico Dukascopy del proyecto
(no incluido en el repo), el mismo sistema da:

| Periodo | Costes | Total | Caída máx | Sharpe |
| --- | --- | --- | --- | --- |
| 2005–2019 | normales | −9.1% | −15.0% | −0.15 |
| 2005–2019 | al doble | −14.5% | −16.5% | −0.25 |
| 2020–2026 | normales | +19.3% | −6.6% | 0.77 |
| 2020–2026 | al doble | +16.0% | −7.0% | 0.64 |

Entre 2005 y 2019 solo EURAUD gana (PF 1.15); NZDUSD pierde un 8%.

## Monte Carlo del challenge FTMO, repetido

Mismo método que `ftmo_montecarlo.py`: bootstrap con reemplazo de los días reales del
portfolio, 5.000 trayectorias de hasta 500 días, objetivo +10%, caída diaria 5% y caída
total 10% medida desde el máximo. Ahora está en `python -m lab.nnfx --monte-carlo 5000`.

Con Dukascopy desde 2020 y el riesgo doble del motor original, el port da 65.5% de P(pass)
y 10.6% de caída P95, cerca del 69.7% y 10.5% del proyecto; la diferencia viene del empate de
USDCHF y del generador aleatorio.

| Datos | Riesgo | Costes | P(pass) | P(fail) | Mediana hasta pasar | Caída P95 |
| --- | --- | --- | --- | --- | --- | --- |
| Resultado previo del proyecto (2020–2026) | 0.8% efectivo | normales | 69.7% | 19.8% | 210 días | 10.5% |
| Dukascopy 2020–2026 | 0.40% | normales | 32.0% | 1.6% | 360 días | 8.3% |
| Dukascopy 2020–2026 | 0.40% | al doble | 25.8% | 2.3% | 361 días | 8.7% |
| Dukascopy 2005–2026 | 0.40% | normales | 7.6% | 5.4% | 383 días | 10.0% |
| Dukascopy 2005–2026 | 0.40% | al doble | 5.5% | 7.2% | 379 días | 10.1% |
| Dukascopy 2005–2019 | 0.40% | normales | 2.8% | 10.0% | 388 días | 10.1% |
| Dukascopy 2005–2026 | 0.80% | normales | 35.3% | 44.9% | 239 días | 10.7% |
| Yahoo 2016–2026 | 0.40% | normales | 3.8% | 9.5% | 384 días | 10.1% |
| Yahoo 2016–2026 | 0.40% | al doble | 2.7% | 12.6% | 372 días | 10.2% |

El resto hasta 100% son trayectorias que no pasan ni fallan en 500 días. Con el riesgo real
del EA y todo el histórico, la probabilidad de pasar baja del 69.7% a un 5–8%, y lo normal es
no llegar al objetivo en casi dos años. Subir el riesgo al 0.8% sube P(pass) al 35%, pero a
costa de fallar el 45% de las veces.

## Conclusión

La ventaja aparece en el periodo en que se eligió la configuración y en la fuente de datos
con que se eligió. En 15 años previos no vistos es negativa, con una caída que superaría el
10% del FTMO, y con otra fuente de datos para el mismo periodo se reduce a EURAUD. Los costes
al doble restan poco (opera ~14 veces al año por par), así que el problema no son los costes
sino la falta de ventaja estable. El Monte Carlo repetido con el riesgo corregido y el histórico desde 2005 lo
confirma: la probabilidad de pasar el challenge queda en torno al 5–8%.
