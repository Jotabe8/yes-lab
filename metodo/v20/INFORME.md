# v20 — VWAP como base de una estrategia: DESCARTADO (0/4 en P1)

24-11-2026. Preregistro en `PREREGISTRO.md` (escrito antes de bajar el volumen). Salidas en `salidas/`.

## Respuesta corta
El VWAP no da una estrategia con ventaja en US100, US500, US30 ni GER40 con costes FTMO. Ninguna de las cuatro
hipótesis pasa P1 (2012-22) y no se abre el fuera de muestra. La razón de fondo: en índices el VWAP es casi
idéntico a la media simple del precio desde la apertura (TWAP), así que las reglas de VWAP son reglas de media
móvil del precio, una familia ya agotada en el proyecto.

## D0 — ¿el volumen cambia algo? No
| Comparación (US100) | corr (P − VWAP)/ATR 10:30 / 12:00 / 14:00 / 15:55 | signo de P − VWAP igual | diferencia mediana |
|---|---|---|---|
| Ticks FTMO (lo que ve el EA) vs QQQ real (SIP) | 0,993 / 0,992 / 0,991 / 0,989 | 97,2 % | 0,016 ATR |
| Sin ponderar (TWAP) vs QQQ real | 0,991 / 0,987 / 0,983 / 0,981 | 96,1 % | 0,023 ATR |
| Ticks FTMO vs TWAP | 1,000 / 0,999 / 0,998 / 0,997 | 98,7 % | 0,007 ATR |

US500 con SPY y US30 con DIA, igual (corr 0,97-0,99, signo 94-97 %). El volumen de ticks de MT5 da prácticamente el
mismo VWAP que el volumen real. La versión con volumen de ticks se parece a la real, así que un EA podría
calcularlo bien, pero no hay nada que calcular: no aporta información frente al precio.

## P1 2012-22, neto de costes (decisión con TWAP ≈ ticks; volumen real de ETF 2016-22 como control)
| Hipótesis | Resultado neto (4 mercados juntos) | Volumen real (ETF, 3 mercados US) | Veredicto |
|---|---|---|---|
| H1 cierre lejos del VWAP → mismo lado al día siguiente | +0,000 R t 0,02; 3 de 4 mercados < 0; coef. de z t −0,74 | −0,038 R t −1,57 | Falla |
| H2 VWAP como stop dinámico del ORB US100 | ΔR −0,048 t −1,39; Sharpe 0,73 → 0,62 (US500 y US30 también peor) | Δ −0,066 t −1,64 | Falla (empeora el ORB) |
| H3 bandas ±2σ, vuelta al VWAP | −0,71 R t −3,3 (bruto ≈ 0; −2,1 pb/op en US100) | −0,20 R t −7,9 | Falla |
| H4 tendencia VWAP (Zarattini y Aziz) M1 / M5 | −10 pb/día t −11,5 / −4 pb/día t −4,2 | −7 / −2 pb/día | Falla |

Notas:
- H4 tiene bruto positivo en US100 (+6 a +11 pb/día, por encima del placebo): es el momentum intradía del US100, el
  mismo que ya cobra el ORB. Con 7-17 giros al día el coste se lo come (neto ≈ 0 en US100, negativo en los otros
  tres). No es una ventaja nueva ni descorrelacionada.
- H2: usar el VWAP como stop corta los ganadores del ORB antes de tiempo; confirma que no hay que tocar el EA.
- H1 (el único mecanismo nuevo, la presión del cierre que sigue al día siguiente): sin señal en ninguna
  ponderación, ni en las mesetas q70 y q90.
- Con ticks FTMO (US100, solo 2021-09 a 2022) los signos son los mismos; muestra corta, solo como comprobación.

## Desviación del preregistro
El volumen de Dukascopy (`dukascopy-node -v`) bajó vacío en GitHub (CSV de 0 bytes) y las CSV del PC no traen
volumen. Se usó en su lugar el volumen de ticks de FTMO de `US100_cash_M1_FTMO.csv` del PC (2021-09 a 2026-09), que
es exactamente lo que vería el EA. Como da el mismo VWAP que el TWAP (corr 0,999), la decisión se toma con TWAP en
los cuatro mercados y con el volumen real de los ETF como control. No cambia el veredicto.

## Qué queda
Nada de la familia VWAP. Se cierra (regla de Jorge: no queda en reserva). Datos nuevos útiles para otros estudios:
barras de 1 min con volumen real de QQQ, SPY y DIA 2016-26 en `datos/etf_*.npz`.
