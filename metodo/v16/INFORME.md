# v16 — 5 sistemas aleatorios en 5 mercados aleatorios y búsqueda de patrones desde los datos

20-11-2026. Pedido por Jorge: preparar al azar 5 sistemas en 5 mercados, estudiar los datos sin
partir de estrategias conocidas y buscar patrones explotables con método científico.

## Veredicto
**Ningún patrón pasa la confirmación. Nada entra al embudo.** Los datos sí tienen estructura que
no es azar (sobre todo un «reloj» horario en EURUSD que persiste fuera de muestra), pero fuera de
muestra mide 0,3-0,6 veces el coste: es real y no se puede cobrar.

## 1. Sorteo (reproducible)
- Universo: las 15 cachés Dukascopy M1 bid/ask completas 2018-26 del PC.
- `numpy.random.default_rng(20261120).choice(universo, 5)` → **EURUSD, UK100, JP225, US500, XAUUSD**.
- M5 en precio medio (UTC). Coste i/v: horquilla FTMO real + 0,2 pb, o media horquilla
  Dukascopy + 0,2 pb si es mayor. Exploración 2018-22, confirmación 2023-01 → 2026-10.

## 2. Los 5 sistemas aleatorios (`fase1_aleatorios.py`)
Hora, duración, stop (0,2-1·ATR14) y regla de dirección sorteados con semilla 20261120+i.

| # | mercado | regla sorteada | neto 2018-22 (R) | t | neto 2023-26 (R) | t |
|---|---|---|---|---|---|---|
| 1 | EURUSD | 12:45, 4 h, sigue el día | −0,056 | −2,07 | −0,050 | −1,57 |
| 2 | UK100 | 11:50, 2 h, contra posición en rango | −0,012 | −1,87 | +0,002 | +0,25 |
| 3 | JP225 | 01:00, 1 h, sigue posición en rango | −0,007 | −0,83 | −0,013 | −1,60 |
| 4 | US500 | 01:35, 6 h, sigue posición en rango | −0,025 | −1,80 | +0,014 | +0,94 |
| 5 | XAUUSD | 19:20, 1 h, contra el día | −0,011 | −2,81 | −0,005 | −1,55 |

Con 2.000 aleatorios más por mercado (10.000): bruto medio 0,000-0,002 R, el neto pierde
exactamente el coste, la distribución del t bruto es la de una moneda (p5/p95 ≈ ±1,7).
**Sesgo de selección medido**: el mejor de N por t en 2018-22 tiene neto +0,03 R con N = 2.000 y
fuera da −0,029 R (positivo fuera solo en el 20 % de los sorteos, igual que al azar). La
correlación del t bruto entre los dos periodos es +0,075: lo que un aleatorio «gana» antes no dice
casi nada de lo que gana después.

## 3. Evolucionar los aleatorios (`fase4_evolucion.py`)
300 mutaciones por ascenso de colina sobre 2018-20 a partir de cada sistema: el t de
entrenamiento sube de −1,6 de media a +1,7; en validación 2021-22 da −0,6 y fuera −0,5. Optimizar
desde el azar fabrica curvas, no ventajas.

## 4. Mapa de exploración 2018-22 (`fase2_mapa.py`)
4.628 pruebas: 5 mercados × vela cada 30 min (horas líquidas) × 1 h / 3 h × 13 condiciones
(todos los días + 6 rasgos medidos antes de entrar × tercio alto/bajo: última hora, día hasta
ahora, ayer, sorpresa de volatilidad, posición en el rango de ayer y movimiento de los otros 4
mercados). Nulo: 50 mapas con el rasgo permutado entre días (o signo aleatorio).

- |t| ≥ 3: **52 reales frente a 27,7 en el nulo** (p95 37) → hay estructura de más.
- 36 de las 52 son EURUSD: sube de 01:00 a 03:00 UTC, cae de 03:30 a 04:30 y cae de 09:00 a 12:00.
- Umbral familiar 5 % (p95 del máximo |t| nulo): 4,92. Solo 1 celda lo supera.
- Regla de selección fijada antes de mirar fuera (|t| ≥ 4 y efecto ≥ 2× coste): 4 candidatas;
  el nulo deja pasar 1,0 de media (p95 3), así que se esperaba ~1 falsa de 4.

## 5. Confirmación 2023-26 (preregistro en commit 7f09137, antes de abrir los datos)
Stop de emergencia 0,5·ATR14, t por semana, listón Bonferroni t ≥ 2,24.

| id | regla | neto exp (R) | neto fuera (R) | t fuera | ×2 | mitades | placebo de hora p | veredicto |
|---|---|---|---|---|---|---|---|---|
| C1 | EURUSD largo 01:30-02:30 si abre en el tercio bajo del rango de ayer | +0,015 | −0,019 | −1,66 | no | no | 0,51 | descartada |
| C2 | EURUSD corto 06:00-07:00 si ayer cayó | +0,029 | −0,022 | −1,78 | no | no | 0,51 | descartada |
| C3 | EURUSD corto 09:00-12:00 todos los días | +0,032 | −0,001 | −0,04 | no | no | 0,05 | descartada |
| C4 | Oro largo 06:30-07:30 si ayer cayó | +0,028 | +0,016 | +1,42 | ≈0 | sí | 0,03 | descartada (t < 2,24) |

C4 es la que más aguanta (63 % del bruto, las dos mitades positivas, gana a su placebo de hora),
pero no llega al listón, con costes ×2 queda en 0 y su neto es +0,016 R/op: aunque pasara, no da
para una prop (hace falta del orden de +0,07 R/op). Según la regla del proyecto, queda descartada.

## 6. ¿Persiste el mapa entero? (`persistencia.py`)
- Correlación del t exploración/fuera en las 4.628 celdas: +0,075 (casi nada).
- Celdas con |t| ≥ 3: el 67 % mantiene el signo fuera, pero su efecto fuera es **0,39× coste**.
- **Reloj horario de EURUSD**: correlación +0,39 entre su perfil horario 2018-22 y 2023-26. Es la
  única estructura que persiste, y coincide con la estacionalidad FX por horario de
  Breedon-Ranaldo (2013): la moneda cae durante su propio horario. La búsqueda v3 la tiró en T0
  sin datos; ahora queda medida: existe, y en las 16 horas con |t| ≥ 2 pasa de 1,07× el
  coste en 2018-22 a 0,26× en 2023-26.
- UK100, JP225, US500 y oro: su perfil horario no persiste (correlaciones −0,42 a +0,15).

## Conclusiones
1. Los sistemas aleatorios pierden justo el coste: es la línea base que cualquier idea tiene que
   superar, y la selección del mejor de miles no la supera fuera.
2. Los datos intradía de estos 5 mercados tienen algo de estructura (el doble de celdas
   «significativas» que el azar), pero se concentra en patrones pequeños que fuera de muestra
   rinden menos que el coste. Coincide con las búsquedas masivas anteriores (25.422 reglas, v2-v4).
3. El único patrón persistente (reloj EURUSD) ya tenía nombre en la literatura y no es operable
   con costes FTMO. Solo se reabriría con un coste ≤ 0,3 pb i/v en EURUSD, que no hay en prop.
4. Lección de método que vale para el futuro: el listón de selección (|t| ≥ 4 y ≥ 2× coste) aún
   deja pasar efectos que se encogen a la mitad o menos; pedir efecto ≥ 3× coste en exploración
   (como P0) habría dejado fuera C1-C3 antes de gastar la muestra.

## Archivos
`datos.py`, `motor.py`, `fase1_aleatorios.py`, `fase2_mapa.py`, `nulo_seleccion.py`,
`PREREGISTRO.md`, `fase3_confirmar.py`, `fase4_evolucion.py`, `persistencia.py`, `salidas/`.
Datos M5 en el PC: `Prop Firm Challenges\aleatorios_20nov\m5_*.npz` (de las cachés Dukascopy).
Para reproducir: copiar esos npz a una carpeta y `V16_DATOS=<carpeta> python -m metodo.v16.fase1_aleatorios`.
