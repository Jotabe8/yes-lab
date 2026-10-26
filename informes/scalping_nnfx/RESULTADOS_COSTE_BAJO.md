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
