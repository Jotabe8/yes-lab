# Buscar un sistema distinto al ORB · resultados (2026-10-30)

Preregistro: `PREREGISTRO.md`. Datos: M1 del PC de Jorge (Dukascopy y FTMO, hora servidor = NY+7),
barras de 30 min con `barras30.py`. n_pruebas total: 41 (t requerido ≈ 3,0).

## Veredicto
**Ninguna de las dos ideas sirve. No hay segundo sistema nuevo.**

| Idea | Puerta | Motivo |
|---|---|---|
| A. Periodicidad intradía (misma media hora de días anteriores), 10 mercados | **P1** | Bruto negativo en 9/10 (A1) y 7/10 (A2); 0 de 20 casillas sobre el p95 del placebo; el coste (1-5 pb) es 4-20 veces el efecto |
| B. Deriva tras el inventario EIA, USOIL | **P3** | Ajuste 2021-22 prometedor, fuera de muestra 2023-26 se apaga y en 2025-26 es negativo |

## A. Periodicidad intradía (Heston, Korajczyk y Sadka)
Media por mercado 2018-22, operando cada media hora de la sesión de contado en la dirección de la
media de esa misma media hora en los 20 días anteriores (A1) o en los mismos días de la semana de 8 semanas (A2):

- A1: bruto medio −0,29 pb por operación; coste medio 2,0 pb. Positivo en 1/10 mercados.
- A2: bruto medio −0,15 pb; positivo en 3/10. Ningún mercado por encima del placebo.
- Si acaso hay algo de reversión (US500 A1 −0,55 pb, t −2,6), pero es una fracción del spread.
Tabla completa: `periodicidad_ajuste.csv`.

## B. Deriva tras el inventario de crudo de la EIA (miércoles 10:30 NY)
Dirección del movimiento 10:30-10:35 NY; entrar a las 10:35 y salir a las 14:30 NY (B2).

| | Ajuste 2021-22 | Fuera de muestra 2023-26 |
|---|---|---|
| Operaciones | 104 | 183 |
| Bruto sin stop | +33 pb (t 2,06) | +11 pb (t 1,08) |
| p95 dirección al azar | +28 pb | +15 pb (no lo supera) |
| Otros días a la misma hora (máx.) | +9 pb | +9 pb |
| Coste (spread FTMO) | 2,5 pb | 5,3 pb |
| Neto con stop 0,5 ATR (elegido antes de abrir el OOS) | +0,099 R (t 1,31) | +0,021 R (t 0,37) |
| Por año (neto, stop 0,5 ATR) | 2021 +0,04 · 2022 +0,15 | 2023 +0,16 · 2024 +0,05 · 2025 0,00 · 2026 −0,11 |

La salida a las 11:30 NY (B1) no funcionaba ni en ajuste (+0,8 pb). En ajuste había meseta
(las 16 combinaciones de ventana 3-15 min y salida 13:30-15:00 eran positivas, 19-39 pb), pero
fuera de muestra caen a −2/+11 pb. Parece un efecto de 2022 (año de petróleo muy volátil) que se
ha ido apagando; además el spread de FTMO en USOIL se ha doblado.

## Qué deja esto
Con estas dos ya son unas 30 familias. Patrón: lo único que sobrevive al coste de un CFD de prop
es el momentum de la apertura de la sesión de contado (ORB). Las reglas de precio de un solo
mercado en otras horas o ventanas no cubren el spread.

## C. Dirección de la sesión de NY con información de otros mercados (`PREREGISTRO_SESION_NY.md`)
Aplicando el mapa de coste: ventana más barata (apertura de contado → cierre), una operación al día,
dirección decidida a las 9:30 NY por una regresión ridge (solo con el pasado) sobre la noche del índice,
el GER40 desde su apertura, oro, USDJPY, EURUSD, US2000−US100 y el día anterior. Ajuste 2019-2022:

| Mercado | Ops | Bruto pb (t) | Coste pb | p95 placebo | Por año |
|---|---|---|---|---|---|
| US100 | 645 | +5,2 (0,99) | 0,9 | +8,8 | 2020 +18 · 2021 +1 · 2022 0 |
| US500 | 659 | +0,4 (0,11) | 1,3 | +4,9 | 2020 +11 · 2021 −1 · 2022 −6 |
| US30 | 657 | +2,0 (0,59) | 0,8 | +5,0 | 2020 +12 · 2021 0 · 2022 −3 |
| US2000 | 659 | −0,3 (−0,06) | 1,9 | +7,6 | 2020 −7 · 2021 +7 · 2022 −3 |

Ninguno supera el placebo; lo poco que hay es 2020. **Descartada en P1** (n_pruebas 4; acumulado 45).
El coste aquí es 1 pb frente a 100 pb de movimiento: la señal sencillamente no predice la dirección.

## D. ORB en otros mercados y otros horarios (`orb_horas.py`)
La regla del ORB en barras de 30 min (dirección del cuerpo de la primera barra, stop 0,15 ATR diario, sin
objetivo, salida al cierre de la ventana), en 11 mercados × 4 aperturas: Tokio (02:00 servidor), Europa
(10:00), datos de EE. UU. (15:30) y NY (16:30). Ajuste 2018-22, placebo con dirección al azar y las mismas salidas.
n_pruebas 44 (acumulado 89). Tabla: `orb_horas_ajuste.csv`.

Calibración: US100 en NY +0,15 R neto (t 2,4) y GER40 en Europa +0,17 R (t 2,3), como los ORB conocidos.

| Casilla | Bruto R | Coste R | Neto R (t) | p95 placebo | Años + |
|---|---|---|---|---|---|
| US100 · NY (el ORB actual) | 0,197 | 0,045 | **+0,152 (2,4)** | 0,122 | 5/5 |
| GER40 · Europa (ORB GER40) | 0,209 | 0,043 | **+0,166 (2,3)** | 0,195 | 5/5 |
| US500 · NY | 0,181 | 0,074 | +0,107 (1,6) | 0,142 | 5/5 |
| GER40 · NY | 0,089 | 0,041 | +0,049 (0,9) | 0,105 | 4/5 |
| US30 · Europa | 0,094 | 0,059 | +0,034 (0,5) | 0,193 | 3/5 |
| JP225 · Tokio | 0,159 | 0,126 | +0,033 (0,6) | 0,146 | 2/5 |
| US100 · Europa | 0,107 | 0,115 | −0,008 | 0,177 | 2/5 |
| Resto (34 casillas) | | | negativo | | |

- **Otros horarios no sirven**: ninguna casilla fuera de la apertura propia de cada mercado supera el placebo.
  El ORB funciona porque la apertura de contado concentra el flujo de órdenes de ese mercado; la apertura
  de otra bolsa no lo hace.
- **Otros mercados en su apertura**: US500 en NY es la única que pasa el placebo (+0,107 R, 5/5 años),
  pero es la misma operación que el US100 (mismo momento, mismo sentido casi siempre): no diversifica y para
  FTMO cuenta como la misma estrategia. JP225 en Tokio supera el placebo antes de costes, pero el spread se
  come el 80 %. Europa (UK100, FRA40, EU50), US2000, oro y petróleo no pasan.
