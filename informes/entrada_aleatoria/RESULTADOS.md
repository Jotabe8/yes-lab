# Entrada aleatoria con gestión de riesgo NNFX (2026-10-26)

**Veredicto: descartado.** La moneda con gestión NNFX no tiene edge en ningún mercado agregado ni periodo,
y el EV por cuota FTMO sale negativo en todas las casillas salvo una optimista (+55 a +134 €/año, 2-Step 100K)
que se vuelve negativa con costes al doble o midiendo el límite diario con el peor punto intradía.

## Qué se probó

- **Entrada:** moneda al 50 % (largo o corto) a la apertura del día siguiente; siempre una posición por mercado,
  se reentra al día siguiente de cerrar. 100 semillas distintas.
- **Gestión** (fijada antes de mirar resultados), ATR(14) D1, riesgo fijo por operación:
  - V0 moneda 1:1: SL = TP = 1,5 ATR (control).
  - V1 NNFX de VP: SL 1,5 ATR, mitad a 1 ATR, resto a BE y trailing de 2 ATR al cierre.
  - V2 NNFX de una orden: SL 1,5 ATR, TP 1 ATR.
  - V3 Van Tharp: stop inicial y trailing de 3 ATR desde el primer día.
  - V4 = V1 con cierre a los 20 días.
- **Mercados:** 11 pares FTMO + oro (MT5 `data/ohlc`, hasta 2026-05) y además 8 índices, plata, WTI, BTC y ETH
  (D1 Dukascopy `data/D1`, hasta 2025-12). 2018-2022 ajuste, 2023-2026 prueba.
- **Costes:** spread + comisión (forex 2,2 pips, oro 0,35 $, índices 0,8-4 pb) y financiación del broker por noche
  (forex 1 %/año, metales e índices 2,5 %, WTI 3 %, cripto 15 %). Al ser la dirección aleatoria, el diferencial
  de tipos se compensa; solo se cobra el recargo. También al doble.
- **Si en una vela tocan stop y objetivo, se cuenta el stop.**

## Resultado del backtest (2018-2026, media de 100 semillas)

| Gestión | Ops/año (24 mercados) | R bruto/op | t bruto | R neto/op | Neto ajuste / prueba | Neto forex+oro |
|---|---|---|---|---|---|---|
| V0 moneda 1:1 | 990 | −0,003 | −1,9 | −0,039 | −0,036 / −0,044 | −0,040 |
| V1 NNFX VP | 622 | +0,007 | +0,5 | −0,034 | −0,029 / −0,042 | −0,052 |
| V2 NNFX 1 orden | 1.397 | −0,004 | −1,2 | −0,033 | −0,036 / −0,027 | −0,037 |
| V3 Van Tharp | 235 | −0,006 | −0,1 | −0,066 | −0,060 / −0,077 | −0,090 |
| V4 VP + 20 días | 725 | +0,006 | +0,7 | −0,032 | −0,024 / −0,044 | −0,047 |

t por bootstrap de bloques de 20 días sobre la serie media de las semillas. El bruto es cero, como debe ser:
la gestión sola no crea ventaja. El coste medio es 0,015 R de spread más 0,02-0,06 R de financiación, porque
en D1 las posiciones duran 4-27 días. Solo 2020 fue positivo (V1 +0,044 R).

**Mercados con tendencia.** Con trailing (V1, V3, V4), oro, BTC, ETH y USDJPY salen positivos (V3: +0,17 R en
ajuste, +0,07 R en prueba). Es seguimiento de tendencia en los activos que más subieron en 2018-2025, elegidos
mirando el resultado; esa familia ya se descartó (TSMOM multiactivo, trend following en forex). No se aprovecha.

## EV por cuota FTMO (presupuesto 632 €, 1 año, mejor riesgo de una rejilla 0,1-1 %)

Neto medio en € con el mejor riesgo. "Cierre" = límite diario y suelo medidos solo al cierre (optimista);
"peor" = sumando el peor punto intradía de cada posición (pesimista). "Media 0" es la misma serie con la media
restada: lo que daría solo la estructura de pago de FTMO si no hubiera costes.

| Serie | 2-Step 100K cierre | 2-Step 100K peor | 1-Step 100K cierre | 2-Step 10K cierre |
|---|---|---|---|---|
| V0 forex+oro | **+55** (P>0 10 %) | −438 | −42 | −89 |
| V0 forex+oro, costes ×2 | −238 | −498 | −221 | −89 |
| V1 forex+oro | −133 | −412 | −162 | −89 |
| V4 forex+oro | −101 | −417 | −128 | −89 |
| V4 24 mercados | −94 | −498 | −242 | −90 |
| Control media 0 (V0 forex+oro) | +1.569 | −81 | +1.032 | +151 |

Subir el riesgo a 1,5-3 % no lo arregla: el mejor caso es +134 € (V0 forex+oro, 2-Step 100K, cierre) y en
"peor" todo es negativo (`ev_riesgo_alto.csv`).

## Por qué sale peor que la moneda de la Prueba 1

La Prueba 1 (`ea-pons-nnfx/prueba1-sin-edge-resultados.md`) daba +381 € en 2-Step 10K con 0,05 R de coste y una
operación al día. Aquí:

1. **La financiación en D1 cuesta tanto como el spread.** El coste real es 0,03-0,07 R por operación, no 0,015.
2. **Muchas posiciones a la vez.** Con 12-24 mercados el coste se suma por operación, pero la volatilidad de la
   cartera crece mucho menos. El arrastre anual llega a −15 a −45 R contra una volatilidad de ~20-30 R, y la
   estructura de FTMO no compensa eso.
3. **El límite diario.** Con varias posiciones abiertas, los días malos coinciden y el 5 % diario salta antes.

La estructura de la prop vale de +1.000 a +1.500 €/año en el control de media cero, pero solo si el coste por
operación es casi nulo. Con estos costes se pierde todo.

## Ficheros

- `aleatoria.py`: backtest (numba), `ev_ftmo.py`: Monte Carlo FTMO, `riesgo_alto.py`: rejilla hasta 3 %.
- `resumen.csv`, `por_año_mercado.csv`, `ev_ftmo_cierre.csv`, `ev_ftmo_peor.csv`, `ev_riesgo_alto.csv`.
- Reproducir: `python3 aleatoria.py DIR_OHLC DIR_D1 SALIDA 100 && python3 ev_ftmo.py SALIDA cierre && python3 ev_ftmo.py SALIDA peor`.
