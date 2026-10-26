# Scalping de coste bajo: las cuatro palancas (2026-10-26)

**Veredicto: hay un indicio, no una prueba.** Una sola casilla pasa todos los filtros pre-registrados: GER40 M30,
retroceso a EMA20 con tendencia y gestión de corredor. Su EV por cuota FTMO es alto (+4.779 €/año en
2-Step 100K, frente a +1.435 € del control de media cero). Pero buena parte de la ganancia aparece también con
dirección aleatoria en las mismas velas. Antes de dar nada por bueno toca pasar por el Strategy Tester con ticks FTMO.

## Reglas (fijadas antes de ver datos, cabecera de `coste_bajo.py`)

- US100 (Dukascopy 2018-22, FTMO 2023-26) y GER40 (Dukascopy 2018-21, FTMO 2022-26), velas M1 bid con spread real.
- M15 y M30. Señal solo en la primera hora y media de contado (US100 16:30-18:00, GER40 10:00-11:30 servidor);
  la posición se cierra como tarde al final de la sesión (22:55 / 18:25). Máximo 2 operaciones al día.
- Filtro de coste: entrar solo si spread / (1,5 ATR) ≤ 0,02 R (con y sin filtro).
- G1 = NNFX de VP (mitad a 1 ATR, BE, trailing 2 ATR). G2 = corredor (a BE a +1 ATR, sin parcial, trailing 2 ATR).
- Entradas: aleatoria (placebo, 20 repeticiones), E1 retroceso a EMA20, E2 ruptura Donchian 20, E3 RSI(2).
- Pasa si: neto > 0 en 2018-22 y 2023-26, t ≥ 2 en 2023-26, neto > 0 al doble de costes y por encima del p95 del placebo.

## Resultado

Las palancas funcionan contra el spread: en la ventana de apertura el coste baja a 0,015-0,05 R por operación,
frente a 0,3-0,4 R del scalping M1. De 48 casillas, solo una pasa:

| GER40 M30 E1 G2 (sin filtro) | 2018-22 | 2023-26 |
|---|---|---|
| Ops/año | 114 | 113 |
| Neto por operación | +0,060 R (t 0,95) | +0,191 R (t 2,13) |
| Costes al doble | +0,020 R | +0,171 R (t 1,93) |
| Placebo aleatorio en cada vela (p95) | 0,061 | 0,061 |

Por años: +0,12 / −0,20 / +0,10 / +0,04 / +0,26 / +0,14 / +0,06 / +0,42 / +0,15 R (2018-2026, 8 de 9 positivos).

**El retroceso a EMA20 en GER40 sale positivo en las 16 variantes** (M15/M30 × G1/G2 × con/sin filtro × dos
periodos), aunque solo esta llega a t ≥ 2. Ninguna casilla de US100 pasa: la ruptura de US100 M15 da t 3,2 en
ajuste y se queda en t 1,1 en prueba.

## Robustez (`robustez_ger40.py`, un parámetro cada vez)

| Cambio | Neto ajuste | Neto prueba (t) | Años + |
|---|---|---|---|
| Original | +0,060 | +0,191 (2,13) | 8/9 |
| Gestión G1 (NNFX VP) | +0,009 | +0,087 (1,51) | 7/9 |
| M15 / M20 / M60 | +0,068 / −0,030 / +0,060 | +0,055 / +0,092 / +0,214 | 8, 4, 7 de 9 |
| EMA rápida 10 / 30 / 50 | +0,093 / +0,004 / +0,039 | +0,158 / +0,169 / +0,078 | 7, 7, 5 de 9 |
| EMA lenta 100 / 400 | +0,061 / +0,032 | +0,223 / +0,183 | 8, 7 de 9 |
| Sin filtro de tendencia | +0,018 | +0,050 (0,91) | 5/9 |
| Ventana 60 / 120 / 180 min | +0,066 / +0,067 / +0,025 | +0,170 / +0,136 / +0,125 | 8, 7, 6 de 9 |
| Máx 1 op/día | +0,051 | +0,159 (1,77) | 8/9 |

Todas las variantes vecinas siguen positivas en prueba salvo M20 en ajuste. **El aviso importante:** el placebo
más duro, que entra en las mismas velas con dirección aleatoria, da +0,096 R de media en prueba (p95 +0,187) y
+0,024 R en ajuste (p95 +0,109). Es decir, la mitad de la ganancia viene de *cuándo* entra y de dejar correr
(días de tendencia en el DAX tras la apertura, la misma familia que el ORB GER40), no de la dirección. La
dirección añade unos +0,04 a +0,10 R y solo roza el p95 en prueba.

## EV por cuota FTMO (`ev_ger40.py`, presupuesto 632 €, 1 año, mejor riesgo 0,5-2 %)

| Serie | 2-Step 10K | 2-Step 100K | 1-Step 10K | 1-Step 100K |
|---|---|---|---|---|
| 2018-26 | +924 € (P>0 63 %) | **+4.779 €** (33 %) | +156 € | +2.084 € |
| Solo 2023-26 | +1.381 € (73 %) | +7.115 € (44 %) | +370 € | +3.752 € |
| Control media 0 (2018-26) | +265 € | +1.435 € | −82 € | +151 € |

El óptimo está al 1,5-2 % por operación (máximo 4 % en un día con dos stops, dentro del 5 % diario).
Correlación diaria con el ORB US100: 0,08. Como siempre, en 2-Step sale mejor que en 1-Step.

## Siguiente paso recomendado

Escribir el EA en MQL5 y pasarlo por el Strategy Tester con ticks reales de FTMO en GER40.cash 2022-2026,
que es la siguiente puerta del flujo. Comprobar también su solapamiento con el ORB GER40 v100.

## Ficheros

`coste_bajo.py`, `robustez_ger40.py`, `ev_ger40.py`, `cb_resumen.csv`, `cb_placebo.csv`, `robustez_ger40.csv`,
`ger40_e1_trades.csv`, `ev_ger40.csv`.

## Prueba en otros mercados (`otros_mercados.py`, 2026-10-26): no se repite

Se aplicaron las mismas reglas de GER40, sin cambiar nada, a 14 mercados más, cada uno a su hora de apertura. Los
índices europeos abren a las 10:00 servidor; los de EE. UU., a las 16:30; JP225, a las 09:00 de Tokio; HK50, a las
09:30 de Hong Kong; y el forex, en la apertura de Londres. El placebo son 20 repeticiones con dirección aleatoria en
las mismas velas. Los costes de los índices salen de Dukascopy, que suele cotizar algo más ancho que FTMO.

| Mercado | Neto 2018-22 | Neto 2023-26 (t) | Años + | Coste R | Placebo 2023-26 (p95) |
|---|---|---|---|---|---|
| GER40 | +0,060 | +0,191 (2,13) | 8/9 | 0,036 | +0,086 (0,202) |
| FRA40 | +0,072 | +0,027 (0,38) | 6/9 | 0,066 | +0,011 (0,109) |
| EU50 | −0,110 | −0,135 | 0/9 | 0,179 | −0,098 |
| ESP35 | −0,259 | −0,162 | 1/9 | 0,196 | −0,171 |
| NLD25 | −0,108 | −0,067 | 1/9 | 0,129 | −0,058 |
| UK100 | −0,040 | −0,138 | 2/9 | 0,087 | −0,089 |
| US100 | +0,040 | −0,016 | 3/9 | 0,030 | −0,076 |
| US500 | −0,041 | −0,064 | 2/9 | 0,053 | −0,029 |
| US30 | −0,003 | +0,008 (0,14) | 4/9 | 0,027 | −0,052 |
| US2000 | −0,019 | −0,020 | 3/8 | 0,046 | −0,000 |
| JP225 | −0,081 | −0,135 | 2/9 | 0,078 | −0,074 |
| HK50 | −0,082 | −0,056 | 2/9 | 0,104 | −0,079 |
| EURUSD | −0,058 | +0,014 (0,19) | 5/9 | 0,090 | −0,062 |
| GBPUSD | +0,024 | −0,082 | 5/9 | 0,100 | −0,138 |
| USDJPY | −0,009 | +0,073 (0,97) | 4/9 | 0,074 | +0,015 |

Fuera de GER40, ningún mercado gana en los dos periodos con t ≥ 1. La dirección de la señal mejora al placebo
en unos mercados y lo empeora en otros, con una media cercana a cero. En esta tanda, además, GER40 queda por
debajo del p95 de su propio placebo (0,191 frente a 0,202).

**Veredicto revisado: descartado.** Lo de GER40 es, con toda probabilidad, la casilla afortunada de 48 más un efecto
de "cuándo entrar" propio del DAX en 2022-2025, ya cubierto por el ORB GER40. No hay un patrón general de
retroceso a la EMA20 en las aperturas.
