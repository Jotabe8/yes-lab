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
