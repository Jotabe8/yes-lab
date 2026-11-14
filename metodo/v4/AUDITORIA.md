# Auditoría del proceso de búsqueda (v4, 13-11-2026)

Se revisó el código (`metodo/embudo.py`, `metodo/robustez.py`, `metodo/v3/*.py`), los datos de origen y las
reglas de seguimiento en real, buscando fallos **que quedaban después** de los arreglos de hoy (partido
ajuste/prueba, costes medidos, precio medio). Scripts en `metodo/v4/auditoria/`.

## Resumen

| # | Fallo | Gravedad | Qué se hizo |
|---|---|---|---|
| 1 | **La regla de parada en real es una moneda al aire** | Alta | Medido; se propone una prueba secuencial |
| 2 | **Todo el universo de búsqueda estaba recortado por FTMO** | Alta | Es el origen de la v4 |
| 3 | Preregistros sobre datos ya vistos y multiplicidad de todo el proyecto | Media-alta | Regla nueva: reserva hacia delante |
| 4 | Deflated Sharpe con unidades mezcladas (bug) | Media | **Corregido** en `embudo.py` |
| 5 | Sesgo de supervivencia en el universo de acciones | Media | Anotado; no reabre nada |
| 6 | Placebo inexistente para estrategias de exposición continua | Media | Placebo de rotación temporal en v4 |
| 7 | Simulador FTMO con días independientes | Baja (para el ORB) | Medido: no cambia nada en el ORB |
| 8 | Deslizamiento del stop en real | Ninguna hoy | Medido con las 14 operaciones reales |

## 1. La regla de parada en real es una moneda al aire (`a2_regla_parada.py`)

La ruta dice "parar si la R media < 0 tras 100 operaciones" y "alerta si < +0,04 R". Con la forma real de las R
del ORB v018 (σ 1,80 R):

| Edge verdadero | P(parar tras 100 ops) | P(alerta) |
|---|---|---|
| +0,12 R (el del backtest) | **25 %** | 33 % |
| +0,06 R | 37 % | 46 % |
| 0 (sin ventaja) | **51 %** | 59 % |
| −0,06 R | 63 % | 72 % |

Una de cada cuatro veces mataría un ORB que funciona, y la mitad de las veces seguiría con uno muerto. Con 100
operaciones el error típico de la media es 0,18 R, más que el edge. **Alternativa:** prueba secuencial de Wald
(H1 = +0,12 R contra H0 = 0, α 5 %, β 20 %): con edge real para por error el 18 % y confirma el 76 %; sin edge
para el 92 %. Pero tarda ~400-700 operaciones (2-3 años). Conclusión práctica: **el rendimiento real no puede
validar ni invalidar el ORB a corto plazo; lo que sí se puede vigilar en semanas es la ejecución**: que cada
operación real coincida en día, lado y R con la réplica Python del mismo día (se hizo en el Strategy Tester con
el GER40: 100 % de lados iguales). Recomendado: sustituir la regla de 100 ops por (a) cruce diario real vs
réplica y (b) SPRT acumulado como freno de fondo.

## 2. El universo de búsqueda estaba recortado por FTMO

De 63 familias del registro, **ninguna** es una prima de riesgo de las que la literatura considera persistentes
(prima de volatilidad, financiación/carry de futuros, carry de materias primas, primas de acciones). No por falta de
ideas: no cabían en una cuenta prop (swap, fin de semana, noticias, 1 posición intradía). Todo el esfuerzo se fue a
**ineficiencias de precio intradía**, que son justo donde la competencia es mayor y el edge menor (0 de 28 en
dirección). Sin restricciones, el orden lógico se invierte: primero las fuentes de pago con un **pagador
identificable** (quién paga y por qué seguirá pagando), después las ineficiencias. Esto es la búsqueda v4.

## 3. Preregistros sobre datos ya vistos y multiplicidad global

- Los preregistros v3 son honestos, pero la **elección** de qué preregistrar se hizo después de ver 2018-2026 en
  hilos anteriores (ORB GER40, JP225, cripto ya habían salido positivos). El listón t ≥ 2,4 supone datos frescos;
  con datos ya mirados el falso positivo real es mayor que el 1-2 % de `potencia.py`.
- Con ~63 familias y 1-2 % de falsos positivos cada una, el proyecto **espera 0,6-1,3 falsos "funciona" solo por
  azar**. El ORB US100 se sostiene porque tiene una réplica independiente (2012-17 bruto t 2,0, datos que no
  sirvieron para elegirlo); cualquier candidato nuevo necesita lo mismo.
- **Regla nueva:** todo candidato que pase la prueba preregistrada entra en **reserva hacia delante**
  (seguimiento en papel con datos posteriores a la fecha del preregistro, mínimo el nº de ops que da el T0) o en
  un segundo instrumento/mercado no mirado, antes de dinero real.

## 4. Bug: Deflated Sharpe con unidades mezcladas (corregido)

`embudo()` llamaba `dsr(neto, n, matriz=variantes)` con `neto` **por operación** y la varianza del Sharpe sacada de
la matriz **diaria**. En una estrategia que opera 1 de cada k días el Sharpe diario es ~1/√k del de la operación,
así que el listón quedaba √k veces más bajo de lo debido (más permisivo). Ahora la serie de la estrategia se pasa
en días del mismo calendario que la matriz. Los tests de `tests/test_embudo.py` y `tests/test_robustez.py` pasan.
No cambia ningún veredicto pasado (el DSR era solo aviso y en el ORB opera casi todos los días).

## 5. Sesgo de supervivencia en acciones

Las 78 acciones de `orb_acciones/datos/` son la lista **actual** de CFD de Dukascopy (incluye ZM, TSLA, NVDA, AMD):
empresas que sobrevivieron y crecieron hasta 2026. Cualquier prueba con sesgo largo sobre ellas está inflada (ya se
vio en el "gap de resultados": +0,14 R en la lista FTMO = selección de tecnológicas). Las pruebas descartadas no se
reabren (el sesgo infla, no esconde), pero una prueba futura positiva en acciones necesita un universo con
deslistadas.

## 6. Placebo para estrategias de exposición continua

El placebo del embudo es "dirección u hora aleatoria con las mismas salidas", pensado para operaciones intradía.
Para una prima (estar expuesto X % de los días) el placebo correcto es **la misma exposición en otros días**:
rotación circular de la serie de exposición (conserva el % de días y la longitud de las rachas). Sin él no se
distingue "el filtro aporta" de "estar expuesto a una prima ya paga". Implementado en los scripts v4.

## 7. Simulador FTMO con días independientes (`a1_bootstrap_dias.py`)

`ftmo_2step` remuestrea días sueltos, lo que rompería las rachas si las hubiera. Con bloques de 5, 21 y 63 días
sobre la serie v018: riesgo 1 %, EV +9.600 € (días sueltos) frente a +8.700-9.700 € (bloques); control con media 0
+1.300-2.000 €. **El ORB no tiene rachas** (autocorrelación de |R| −0,03), así que no cambia nada. Para primas de
riesgo (volatilidad agrupada) hay que usar bloques; queda anotado para P4.

## 8. Deslizamiento del stop en real

Las 8 operaciones reales que tocaron el stop dieron −0,93 a −1,06 R (media −0,99 R): el supuesto de las
simulaciones (salida al precio del stop, o a la apertura si hay hueco) se cumple. Muestra pequeña (14 ops).

## Lo que se revisó y está bien

ATR siempre con un día de retraso y en el calendario correcto (servidor NY+7 frente a hora local); stop vela a vela
con huecos a la apertura; fines de semana fuera en cripto; fórmula de años necesarios de T0; costes de FTMO medidos.
