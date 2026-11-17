# Preregistro v13 · ORB "en juego" en aperturas propias fuera del US100 (16-11-2026, antes de ver los datos)

## Por qué esta y no otra (resumen del mapa, ver MAPA_V13.md)
El ORB US100 es la única ventaja. La familia "apertura propia + stop corto" se probó **sin condición** en GER40,
UK100, JP225, oro, crudo y Asia: ninguna pasa (GER40 t 1,58; JP225 bruto real pero coste). El mecanismo que
Zarattini, Barbon y Aziz (2024) documentan en acciones es más estrecho: el ORB **solo funciona en los días "en
juego"**, cuando el volumen relativo de la apertura es anómalo (atención/información nueva concentrada en la
apertura). En acciones lo probamos con coste de acciones (clase B por coste), **nunca en índices, oro o crudo**.
Hipótesis: en mercados donde el ORB incondicional no llega, el subconjunto de días con actividad anómala en el
rango de apertura sí tiene inercia suficiente. Se opera en otras horas y otros activos que el US100 → baja
correlación esperada.

## Mercados (hora local de su apertura propia) y coste FTMO por operación
| Mercado | Dukascopy | Zona | Apertura | Salida | Coste (% del precio) |
|---|---|---|---|---|---|
| GER40 | deuidxeur | Europe/Berlin | 9:00 | 17:25 | 0,0052 |
| UK100 | gbridxgbp | Europe/London | 8:00 | 16:25 | 0,0079 |
| JP225 | jpnidxjpy | Asia/Tokyo | 9:00 | 14:55 (15:25 desde 05-11-2024) | 0,0157 |
| XAUUSD | xauusd | America/New_York | 8:20 (COMEX) | 13:25 | 0,0110 (horquilla 0,0099 + comisión) |
| USOIL | lightcmdusd | America/New_York | 9:00 (NYMEX) | 14:25 | 0,0500 (horquilla CFD estimada) |
Horquillas: tabla medida en el MT5 de FTMO (metodo/v3/spread_aperturas_ftmo.csv); USOIL no medido, se usa
0,05 % (conservador). Informativo: US100 9:30-15:55 NY (no decide nada; el EA no se toca).

## Regla (la del v018 trasladada, sin optimizar)
Precio medio (bid+ask)/2 de M1 Dukascopy, 2012-01 → 2026-11. Rango = 10 primeros minutos tras la apertura.
Lado = cuerpo del rango (si |cierre−apertura| < 10 % del rango, no opera). Entrada a la apertura del minuto 10.
Stop 0,15 × ATR(14) de la sesión (días anteriores). Sin objetivo. Salida a la hora de la tabla. Stop vela a vela,
huecos a la apertura de la vela. Una operación al día y mercado. Riesgo 1 R por operación.

**Condición "en juego"** (se calcula con datos hasta el minuto 10, sin mirar el futuro):
- **V1 (principal) volumen:** RVOL = volumen (bid, Dukascopy) de los 10 minutos del rango / media del mismo
  tramo en los 14 días hábiles anteriores. En juego si RVOL ≥ 1,5.
- **V2 rango:** RRANGO = (máx − mín del rango) / media de los 14 días anteriores. En juego si RRANGO ≥ 1,5.
- Si un mercado no tiene volumen útil (> 20 % de tramos con volumen 0), sale de V1 (no de V2).
Solo hay estas 2 variantes (+ costes ×2 como prueba de robustez). Umbral 1,5 fijado ahora, no se mueve.

## Cartera y criterios (todos a la vez) — V1 decide; V2 solo puede pasar con el listón de 2 pruebas
Cartera = los 5 mercados con 1 R cada operación; serie diaria = suma de R del día.
1. t neto (por operación) ≥ 2,4 en 2012-2026 (V2: ≥ 2,64 por ser la 2.ª prueba).
2. Segunda mitad (2019-07 → 2026-11) neto > 0.
3. Costes ×2 neto > 0.
4. **Placebo de días:** media neta en juego > percentil 95 de 2.000 subconjuntos al azar del mismo tamaño
   (por mercado) sacados de los días con señal ORB. Es lo que separa "en juego" de "ORB sin más".
5. **Placebo de lado:** el lado contrario en los días en juego da < 0 neto.
6. Al menos 3 de los 5 mercados con neto > 0.
7. Correlación diaria con el ORB US100 v018 (serie_v018_be.csv) < 0,3.
Monte Carlo (informativo, decide el tamaño, no el pase): remuestreo por bloques de 20 días de la serie diaria →
P(media ≤ 0), peor DD p95 en R, y Sharpe de v018 + cartera.

Si no pasa: clase en el registro (A sin bruto, B coste, C potencia, D cae en 2.ª mitad), **sin rescates ni nuevos
umbrales**. Si pasa: P4-P6 del embudo (MQL5, Strategy Tester con ticks FTMO) y decide Jorge.

## T0 (potencia)
En juego ≈ 15-25 % de los días → ~40-60 ops/año por mercado, ~250/año la cartera, ~3.500 ops en 14 años.
Con σ ≈ 1,8 R el mínimo detectable con t 2,4 y potencia 80 % es ≈ 3,24·1,8/√3500 ≈ 0,10 R neto: del tamaño
del ORB US100. Pasa T0 (justo).
