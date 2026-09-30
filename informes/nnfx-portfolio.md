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

## Conclusión

La ventaja aparece en el periodo en que se eligió la configuración y en la fuente de datos
con que se eligió. En 15 años previos no vistos es negativa, con una caída que superaría el
10% del FTMO, y con otra fuente de datos para el mismo periodo se reduce a EURAUD. Los costes
al doble restan poco (opera ~14 veces al año por par), así que el problema no son los costes
sino la falta de ventaja estable. Antes de arriesgar la cuenta de un challenge convendría
repetir el Monte Carlo con el riesgo corregido y con el histórico desde 2005.
