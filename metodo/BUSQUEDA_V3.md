# Cómo buscamos, revisado con números (búsqueda v3, 13-11-2026)

Este documento no repite el diagnóstico de `BUSQUEDA_V2.md` (mecanismo antes que datos, ≤ 10 pruebas por
idea, más historia); lo mide y lo convierte en un proceso con cuentas concretas. Código en `metodo/v3/`.

## 1. Resumen en cinco líneas

1. **El embudo actual tira la mitad de los edges reales.** Un edge del tamaño del ORB (+0,12 R/op) pasa
   P1-P3 solo el 46 % de las veces; uno de +0,10 R, el 31 %. Partir 9 años en ajuste y fuera de muestra y
   exigir t ≥ 2 en cada trozo gasta casi toda la potencia.
2. **Gastamos el esfuerzo donde no hay nada.** 28 de las 60 familias probadas eran apuestas de dirección con el
   propio precio: 25 sin señal ni antes de costes, 0 éxitos. Las ideas de volatilidad con pago convexo fueron
   15: los 2 éxitos y 5 que pasaron el ajuste.
3. **Una de cada seis ideas tenía señal real y la mató el coste del CFD de FTMO**, pero nunca preguntamos
   dónde era más barata. Y 13 ideas tenían ≤ 30 operaciones al año: imposibles de validar aunque fueran reales.
4. **Proceso v3:** triaje aritmético antes de tocar datos, el lugar más barato operable antes que la señal,
   simular en precio medio y poner los costes después, una sola prueba preregistrada sobre toda la historia
   limpia, y un registro con el motivo de cada descarte.
5. **Demostración:** 5 ideas descartadas sin datos en minutos; el ORB cripto, que se dio por muerto hoy,
   resulta ser un edge real (t 3,0, corr 0,08 con el ORB) **cuyo único problema es el lugar**. Hoy no hay
   dónde operarlo, pero ahora sabemos exactamente qué coste lo haría operable.

## 2. Qué medí

### 2.1 Potencia del embudo (`v3/potencia.py`)

Series simuladas con la forma real de las R del ORB v018 (σ 1,8 R, asimetría, 31 % de aciertos), centradas y
con un edge verdadero conocido. Probabilidad de que el edge **real** sobreviva:

| Edge real (R/op) | Embudo actual (ajuste 5 años + OOS 3,8) | v3: toda la historia (11 años), preregistrado | v3 con el mismo mecanismo en 3 mercados | Embudo actual, idea de 12 ops/año |
|---|---|---|---|---|
| 0,05 | 6 % | 13 % | 28 % | 1 % |
| 0,08 | 17 % | 38 % | 72 % | 0 % |
| 0,10 | 31 % | 62 % | 89 % | 1 % |
| **0,12 (ORB)** | **46 %** | **81 %** | **98 %** | 1 % |
| 0,15 | 69 % | 96 % | 100 % | 2 % |

Falsos positivos (sin edge, eligiendo la mejor de k variantes): con k = 1-3 el embudo actual da 0,4-0,9 % y
v3 1,0-1,7 %. **v3 dobla la potencia a cambio de ~1 punto de falsos positivos, siempre que se miren ≤ 3
variantes.** Con 10 variantes v3 sube al 8 %: por eso el preregistro y el límite de variantes son obligatorios.

Operaciones necesarias para ver un edge con 80 % de probabilidad (t ≥ 2,4, σ 1,8 R): 0,10 R → 3.400 ops
(16 años a 210 ops/año); 0,15 R → 1.500 (7 años); 0,20 R → 850 (4 años). **Con 12 ops/año, ninguna idea
es verificable en una vida.**

### 2.2 Registro de las 60 familias probadas (`v3/registro_ideas.csv`)

Cada descarte con su **motivo**, que hasta ahora se perdía bajo "descartado":
A sin señal ni antes de costes · B señal bruta real que el coste anula · C imposible de verificar (pocas
operaciones) · D pasó el ajuste y cayó fuera de muestra · E artefacto de datos o del backtest · F funciona ·
G lo mata una regla o el swap de la firma.

| Tipo de idea | A | B | C | D | E | F | G | Total |
|---|---|---|---|---|---|---|---|---|
| Dirección con el propio precio | 25 | 1 | 0 | 1 | 1 | 0 | 0 | 28 |
| Volatilidad / pago convexo | 5 | 2 | 0 | 5 | 1 | **2** | 0 | 15 |
| Calendario | 1 | **7** | 3 | 0 | 0 | 0 | 0 | 11 |
| Estructura de la firma / otras | 4 | 0 | 0 | 0 | 0 | 0 | 2 | 6 |

| Origen | Probadas | Éxitos | Con señal bruta (B + D + F) |
|---|---|---|---|
| Artículo publicado | 28 | 0 | 9 |
| Folklore / gurú | 13 | 0 | 1 |
| Minería de datos | 7 | 0 | 3 |
| Mecanismo propio | 10 | **2** | 5 |

## 3. Los sesgos del proceso (lo nuevo sobre BUSQUEDA_V2)

1. **Embudo sin potencia, veredictos definitivos.** Se trocea una muestra ya pequeña y se exige t ≥ 2 en cada
   trozo. Resultado: la mitad de los edges reales mueren (§2.1), y las 6 ideas de clase D (pasaron el ajuste
   y cayeron fuera) no se pueden distinguir de falsos negativos. Con la regla "no se deja nada en reserva",
   cada falso negativo es permanente.
2. **El esfuerzo sigue a las peticiones, no a la tasa de acierto.** Casi la mitad de las pruebas fueron
   dirección con el propio precio (0 de 28). La familia que funciona (volatilidad en la apertura propia con
   stop corto) tuvo un acierto de 7 de 15 en el ajuste.
3. **El coste se mide solo en el CFD de FTMO.** 10 ideas tenían señal bruta real (gotobi +0,106 R, víspera de
   festivo, deriva nocturna, ORB cripto, ORB de acciones...) y se descartaron por el coste de **un** lugar.
   Nunca se preguntó "¿dónde es más barata?". El coste depende del lugar tanto como la señal del mercado.
4. **Ideas inútiles aunque fueran verdad.** 13 de 60 tenían ≤ 30 ops/año (Halloween, cambio de mes, OPEX,
   víspera de festivo, Fed...). Ni se pueden verificar ni mueven una cuenta prop: 9 ops × 0,04 R = 0,4 R al
   año frente a ~25 R del ORB. Se pueden descartar con una multiplicación.
5. **Los artefactos crean edges y también los matan.** Ya conocíamos dos (stop recortado a −1, precios rancios
   de Yahoo). Hoy apareció un tercero: la prueba del ORB cripto entraba a ask y comprobaba el stop en bid con
   horquillas de Dukascopy de 0,2-6 R; el "bruto" reconstruido (r + spread) salía +1,66 R en 2018-22, y el
   neto en el CFD se calculó con la horquilla de Dukascopy, no con la de FTMO. **Regla: simular siempre en
   precio medio y aplicar después el coste de cada lugar.**

## 4. El proceso v3

Sustituye P0-P3 de `METODO.md`; P4-P6 no cambian.

| Paso | Qué se hace | Se descarta si |
|---|---|---|
| **T0 Triaje aritmético** (5 min, sin datos, `v3/triaje_p0.py`) | Con la estimación previa del edge (la de un artículo se **divide por 2**), ops/año, σ y el coste del lugar **más barato operable**: (1) años necesarios = ((2,4+0,84)·σ/μ_neto)² / ops_año; (2) margen μ_bruto / coste; (3) valor = ops_año × μ_neto. | años > historia limpia disponible; margen < 2; valor < 8 R/año (un tercio del ORB). |
| **T1 Prioridad** | Orden de prueba: (a) volatilidad / pago convexo en una apertura o evento propio, (b) señales de clase B en un lugar más barato, (c) calendario con frecuencia alta, (d) dirección solo con **información nueva** (no el propio precio). | Dirección con el propio precio a horas fijas: ya cubierta por 25.000 reglas, atlas y ML. |
| **T2 Lugar primero** | Tabla de costes por lugar (CFD FTMO, FTMO Futures/CME, otras firmas) y por tamaño de contrato frente a la pérdida máxima de la cuenta. La señal se evalúa en el lugar más barato **donde se pueda dimensionar**. | No hay lugar con coste ≤ la mitad del bruto y tamaño compatible. |
| **T3 Simulación limpia** | Siempre en precio medio, stop vela a vela con huecos a la apertura; costes por lugar después. Placebos: lado contrario **y** misma operación a otra hora. | — |
| **T4 Prueba única preregistrada** | Preregistro escrito y commit antes de los datos: ≤ 3 variantes, toda la historia limpia, mismo mecanismo agrupado en todos los mercados donde aplique. | t neto < 2,4; segunda mitad ≤ 0; costes ×2 ≤ 0; no supera a ninguno de los dos placebos. |
| **T5 Registro** | Fila en `v3/registro_ideas.csv` con clase A-G, efecto estimado y, si es B o C, **qué tendría que cambiar** (coste, historia, lugar) para reabrirla. | — |

Notas: la regla de Jorge de no dejar estrategias "en reserva" se mantiene: una B o C no se opera ni se
retoca. Solo se reabre si cambia el hecho concreto anotado (un lugar más barato, más historia), con una
prueba nueva preregistrada. P4 (EV por cuota frente al control) sigue siendo la puerta final.

## 5. Demostración con dos candidatos

### 5.1 Triaje T0 de cinco ideas sin tocar datos (`v3/triaje_p0.py`)

| Idea | Ops/año | Neto previsto | Años necesarios | R/año | Veredicto |
|---|---|---|---|---|---|
| Deriva pre-FOMC (24 h antes, US500) | 8 | +0,155 R | 55 | 1,2 | fuera (potencia, valor) |
| Víspera de festivo en futuros ES | 9 | +0,034 | 1.009 | 0,3 | fuera |
| Gotobi en futuros 6J | 70 | +0,046 | 71 | 3,2 | fuera (6J cuesta ≈ CFD) |
| ORB de Tokio en futuros NKD | 220 | +0,059 | 44 | 13 | fuera (margen, potencia) |
| OPEX: seguir la mañana | 12 | +0,08 | 137 | 1,0 | fuera |
| **ORB cripto en futuros CME** | 250 | +0,165 | 5 | 41 | **pasa a prueba** |

Cinco ideas cerradas en minutos que con el método anterior habrían costado un hilo cada una.

### 5.2 ORB de la apertura de NY en BTC/ETH, por lugar (`v3/cripto_*.py`, datos `v3/orb_cripto_medio/`)

Clase B de esta mañana (descartado por el coste del CFD). Rehecho con la simulación limpia (precio medio,
M1 Dukascopy descargado con GitHub Actions) y preregistro en el commit `c974bce`: rango 10 min, cartera
BTC + ETH en contratos estándar de CME, 2021-03 → 2026-11.

| | BTC | ETH |
|---|---|---|
| Bruto lado de la vela 2021-26 | +0,235 R (t 3,2) | +0,253 R (t 3,5) |
| Lado contrario (placebo 1) | +0,127 | +0,178 |
| Misma operación a la 01:00 NY (placebo 2) | +0,086 | +0,073 |
| Neto contrato estándar CME (5 BTC / 50 ETH) | +0,189 (t 2,6) | +0,212 (t 2,9) |
| Neto micro CME (MBT / MET) | +0,058 (t 0,8) | −0,31 |
| Neto CFD FTMO (0,065 % + horquilla 0,01-0,03 %) | +0,06 a +0,01 | +0,12 a +0,08 (t 1,2-1,7) |

- **Cartera principal: +0,195 R/día, t 2,98; primera mitad +0,24 y segunda +0,15; costes ×2 +0,15 (t 2,3);
  correlación diaria con el ORB US100 0,08.** Pasa la prueba preregistrada.
- El edge **no está en elegir el lado** (exceso sobre el lado contrario +0,04, t 0,8) sino en la **ventana**:
  a las 9:30 NY cualquiera de los dos lados con stop corto gana +0,18-0,22 R; a la 01:00 NY, +0,06-0,08.
  Es la llegada del flujo de EE. UU. que convierte el día en tendencia, el mismo mecanismo que el ORB.
- 2018-20 bruto también positivo (+0,14 / +0,18 R), pero neto negativo por el coste en R de entonces (igual
  que el ORB US100 en 2012-17).
- **Por qué no es operable hoy:** en FTMO Futures (100K, pérdida máxima 3.500 $ trailing) un contrato
  estándar arriesga ~2.000 $ (BTC) o ~800 $ (ETH): la mitad o un cuarto de toda la pérdida permitida en una
  sola operación. Los micros sí caben, pero sus tasas (MBT ≈ 3,2 $ ida y vuelta para ~40 $ de riesgo) se
  comen el edge. En el CFD de FTMO, BTC no da y ETH queda en +0,08-0,12 R con t < 2.
- **Clase B confirmada, con el disparador exacto para reabrirla:** un lugar con BTC/ETH a coste total
  ≤ 0,02 % ida y vuelta y apalancamiento ≥ 1:2, o una cuenta de futuros con pérdida máxima ≥ 15.000 $.
  Vale la pena mirar la horquilla real de ETHUSD en el MT5 de FTMO entre 9:30 y 16:00 NY: si fuera
  ≤ 0,01 %, ETH en el CFD quedaría en +0,12 R, que justificaría una prueba preregistrada propia.

## 6. Qué cambia a partir de ahora

1. Antes de abrir un hilo de prueba: fila en el triaje T0. Si no pasa, se anota y no se prueba.
2. Orden de búsqueda: mecanismos de apertura o de evento propio con pago convexo, y luego lugares más
   baratos para las B del registro. Dirección con el propio precio, solo con información nueva.
3. Una prueba única preregistrada sobre toda la historia limpia; nada de partir en ajuste y fuera de muestra
   salvo que se miren más de 3 variantes.
4. Cada lugar nuevo que aparezca (firma, contrato, comisión) se cruza con las B del registro antes que con
   ideas nuevas: es la búsqueda más barata que tenemos.
