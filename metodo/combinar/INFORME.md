# Qué se está haciendo mal al buscar ventaja, y cómo combinar indicadores (14-11-2026)

Parte de la auditoría v4 (8 fallos, PR #26) sin repetirla. Aquí van las cosas que se le escaparon, medidas con los
datos del proyecto, y una prueba preregistrada de combinación de indicadores hecha hoy.

## Resumen

1. **El listón no es demasiado alto: la ventana es demasiado corta.** El propio ORB v018 que opera en real da
   **t 1,15 en 2018-2022**; con el listón actual (t ≥ 2,4) se habría descartado. Su significación sale de 2023-2026
   (t 3,06). La versión simple del mismo mecanismo con 15 años (2012-2026) da bruto t 4,38. Cinco años no
   bastan para ver un edge del tamaño del ORB; quince sí.
2. **El fallo principal está en de dónde salen las ideas, no en el filtro.** De 79 familias registradas, 40 no tienen
   ni bruto (clase A) y 1 funciona. Con esa tasa de base, bajar el listón solo fabricaría falsos positivos.
3. **"No lo sé" se trata como "no".** 12 familias (clase C) se descartaron por falta de potencia, no por evidencia en
   contra (el ORB GER40 entre ellas). La regla de no dejar nada en reserva las convierte en descartes definitivos.
4. **El EA en real es una versión afinada que está menos probada que el mecanismo simple.** En 2018-2022 la réplica
   simple da +0,245 R neto (t 3,07) y la serie v018 +0,063 R (t 1,15). Sus parámetros extra se eligieron viendo 2023-2026.
5. **Las combinaciones de indicadores se han probado mucho (25.000 reglas, 4.960 combos NNFX, ML con 20 variables,
   atlas de 3.696 celdas, sistema forex de 4 capas), pero siempre con información del propio precio.** Combinar
   señales redundantes sin ventaja propia no crea ventaja. La única arquitectura de combinación con sentido es
   **primaria con ventaja + información distinta para el tamaño** (meta-etiquetado). Probada hoy con el ORB + gamma
   de opciones (GEX): **no pasa** (parecía t 2,47 en 2012-2018 y desaparece en 2019-2026).

## 1. ¿Mataría el listón al ORB? Sí, si se mide con cinco años

Serie real v018 (`datos/serie_v018_be.csv`) y réplica simple 2012-2026 (`datos/orb_us100_2012_2026.csv`):

| Periodo | v018 real: R/op | t | Réplica simple neta FTMO: R/op | t |
|---|---|---|---|---|
| 2012-2017 | — | — | +0,030 | 0,47 |
| 2018-2022 | +0,063 | **1,15** | +0,245 | 3,07 |
| 2023-2026 | +0,202 | 3,06 | +0,146 | 1,68 |
| Todo | +0,124 (2018-26) | 2,93 | +0,135 (2012-26) | 3,08 |

Con σ ≈ 1,8-2,5 R por operación, el error de la media en 5 años (~1.000 ops) es 0,06-0,08 R: del mismo tamaño que el
edge. Cualquier ventana de 4-5 años da t entre 0,5 y 3,5 para el mismo edge real; lo decide el azar. Esto ya lo
calculó la v3 (`potencia.py`: el embudo antiguo deja pasar un edge de 0,12 R el 46 % de las veces), pero muchas
pruebas posteriores se siguieron haciendo con 2018-2022 + 2023-2026; la de hoy en forex usó solo 2018-2026 cuando
Dukascopy tiene forex desde 2003.

**Regla:** 5 años solo sirven para triaje de clase A (¿hay bruto?). La prueba que decide se hace con toda la
historia disponible (índices US desde 2011-2012, forex desde 2003) o en 3 mercados con el mismo mecanismo.

## 2. El filtro es razonable; las ideas no

Registro (`v3/registro_ideas.csv`): A 40, B 11, C 12, D 10, E 3, G 2, F 1. Probabilidad de que un "pasa" sea real
con la tasa de base del proyecto (1 de cada 30-80 ideas):

| Prueba | Tasa de base 3 % | 5 % |
|---|---|---|
| Embudo antiguo, 1 variante (pasa poco: potencia 46 %) | 0,78 | 0,86 |
| Prueba única v3, 1 variante | 0,71 | 0,81 |
| Prueba única v3, se elige la mejor de 10 | **0,23** | 0,34 |

El riesgo no está en el listón sino en mirar varias variantes y quedarse con la mejor. Bajar el listón no
compensa: con una idea real de cada 30-80, un listón más bajo llenaría el proyecto de sistemas falsos.

Lo que sí falla es el origen de las ideas: 33 de 79 familias son "dirección a partir del propio precio" en mercados
muy líquidos, donde compiten los fondos con más medios. Ninguna ha funcionado.

## 3. "Sin potencia" no es "sin ventaja"

Las 12 de clase C se descartaron porque la historia no daba para ver un edge de su tamaño, no porque se viera que no
lo tienen. Mantener la regla de Jorge (no operar nada en reserva) pero distinguir en el registro "descartada por
evidencia" de "no medible", con su disparador de reapertura (más historia, lugar más barato). Ya existe el campo; la
mejora es no volver a gastar tiempo en ideas cuyo T0 dice que harían falta > 15 años.

## 4. El EA afinado frente al mecanismo simple

La v018 añade cosas (punto muerto a +2 R, filtro ATR p90, etc.) elegidas con 2023-2026 a la vista. Su correlación
con la réplica simple es 0,74 y en 2018-2022 rinde la cuarta parte. No es motivo para cambiar nada en real (la serie
es corta para distinguirlas), pero sí para: (a) no tomar los +0,12 R de la v018 como el edge esperado, sino algo
más cerca de la réplica sin afinar en años no mirados; (b) cuando se monte otra cuenta, valorar la versión con menos
parámetros.

## 5. Cómo combinar indicadores para que tengan ventaja

### Cuándo combinar aporta y cuándo solo sobreajusta

- Ley fundamental (Grinold-Kahn): combinar k señales con capacidad predictiva IC cada una y correlación ρ entre
  ellas da IC × √(k / (1 + (k−1)ρ)). **Si IC ≈ 0, el resultado es ≈ 0 por muchas que se sumen.** Con indicadores
  del mismo precio (media móvil, Donchian, RSI, ATR) ρ ≈ 0,7-0,9: cuatro indicadores mejoran solo un 5-10 %.
- Votación/ensemble (Condorcet): mejora solo si cada votante acierta más del 50 % por sí solo y se equivocan en días
  distintos. Varios votantes al 50 % siguen al 50 %.
- Cada filtro añadido son grados de libertad: el forex de 4 capas mejoró el ajuste (+0,026 → +0,076 R) y empeoró
  fuera de muestra (−0,05 → −0,10 R). Es la firma del sobreajuste.

### Familias de información (lo que de verdad hay que combinar)

| Familia | Ejemplos | ¿Usada en el proyecto? |
|---|---|---|
| Precio propio | tendencia, reversión, volatilidad, rangos | Sí, casi todo (0 de 33 en dirección) |
| Calendario / evento | apertura, FOMC, fin de mes, subastas | Sí; la apertura es la única que paga (ORB) |
| Volatilidad implícita | VIX, VIX9D/VIX | Sí, en el atlas (0 supervivientes) |
| Posicionamiento / flujo obligado | gamma de opciones, COT, flujos de ETF, rebalanceos | Poco: gamma hoy (2 pruebas), COT en forex |
| Otros mercados | tipos, dólar, crédito | Poco (sesión NY con ridge: nada) |
| Microestructura | volumen, desequilibrio de órdenes | No (no hay datos fiables en CFD) |

### Receta

1. **Primaria con ventaja propia**, demostrada sola con historia larga (hoy solo el ORB US100).
2. **Cada indicador añadido viene de otra familia** y tiene un mecanismo de por qué cambia el pago de la primaria.
3. **Se prueba solo, condicionado:** ¿parte la R de la primaria en grupos distintos? Preregistrado, ≤ 3 cortes.
4. **Se usa para el tamaño, no como filtro duro**, y se juzga por la Sharpe con la misma exposición media (quitar
   días baja el total; ya pasó con el filtro de hueco).
5. **Placebo propio:** la misma variable desplazada en el tiempo (conserva su forma, rompe la relación).
6. **Réplica en una serie no mirada** (otra versión del sistema o otro mercado).
7. Nunca: apilar filtros de precio sobre una base sin ventaja.

### Prueba hecha hoy: ORB US100 + gamma (GEX) para el tamaño

Preregistro subido antes de mirar (`PREREGISTRO_META_GEX.md`): tamaño 1,5 / 1 / 0,5 según la GEX del día anterior
esté en el tercil bajo / medio / alto de los 252 días previos. Mecanismo: con gamma negativa los creadores de mercado
alargan las rupturas. Resultado (`meta_gex_salida.txt`):

| | R tercil bajo | medio | alto | Diferencia bajo − alto | t |
|---|---|---|---|---|---|
| 2012-2026 neto | +0,180 | +0,250 | +0,023 | +0,157 | 1,47 |
| 2012-2018 | +0,247 | +0,203 | −0,126 | +0,373 | **2,47** |
| 2019-2026 | +0,117 | +0,289 | +0,133 | −0,016 | −0,11 |
| Serie real v018 2018-26 | +0,115 | +0,230 | +0,052 | +0,063 | 0,59 |

Placebo: la mejora de Sharpe (+0,005) queda justo sobre el p95 (p 0,04), pero falla t ≥ 2,4, falla el signo en la
segunda mitad y falla la réplica. **DESCARTADO.** Es un ejemplo de manual del punto 1: con solo 2012-2018 habría
pasado el listón; con la segunda mitad desaparece.

## Qué recomiendo

1. Toda prueba que decida usa la historia completa (índices desde 2011-2012, forex desde 2003) o 3 mercados con el
   mismo mecanismo; 5 años solo para triaje.
2. Dejar de generar ideas a partir del precio propio. Solo entran ideas con información nueva o con un pagador
   identificable, y la combinación de indicadores solo como meta-etiquetado de una primaria con ventaja.
3. En el registro, separar "descartada por evidencia" de "no medible".
4. Tomar como edge esperado del ORB el de la réplica simple en años no mirados, no los +0,12 R de la v018.
5. Con lo que hay hoy, el mejor uso del tiempo sigue siendo escalar el ORB US100 en más firmas: su capacidad entre
   firmas es mucho mayor que la de cualquier candidato visto.

Fuentes: López de Prado, *Advances in Financial Machine Learning* (meta-etiquetado, "el backtest no es una
herramienta de investigación", importancia de variables antes que reglas); Bailey, Borwein, López de Prado y Zhu
(2014) y Bailey y López de Prado (2014, Deflated Sharpe); Aronson, *Evidence-Based Technical Analysis* (sesgo de
minería de datos, 6.402 reglas sin ventaja en el S&P 500); Harvey y Liu (2015); Grinold y Kahn, *Active Portfolio
Management* (ley fundamental); Chan, *Algorithmic Trading*; Davey, *Building Winning Algorithmic Trading Systems*;
Barbon y Buraschi, *Gamma Fragility*.
