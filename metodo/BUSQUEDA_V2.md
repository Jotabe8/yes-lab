# Cómo buscamos y por qué falla (diagnóstico del 13-11-2026) · Búsqueda v2

## Diagnóstico: qué tienen en común las ~30 familias descartadas

| Patrón | Ejemplos | Por qué falla |
|---|---|---|
| **Origen de la idea: anomalía publicada o folklore de trading** | RSI(2), cambio de mes, Halloween, prima nocturna, ORB en acciones, tug of war, NNFX, Pons | Lo publicado sobre mercados líquidos ya está arbitrado o era de valores pequeños; en lo que ofrece una prop queda en 1-5 pb, el tamaño del ruido. |
| **Una regla fija = una familia entera** | Cada hilo: una idea, un parámetro, sí/no | Bien contra el sobreajuste, pero con poca potencia: un efecto real y condicional (solo con volatilidad alta, solo ciertos días) se diluye en la media de todos los días y la regla muere. |
| **Solo dirección, solo el precio del propio mercado** | 25.000 reglas de seguir/contra a horas fijas | Es el espacio más minado del mundo. Lo que sí es predecible intradía es la **volatilidad** (hora, eventos, régimen) y eso no lo condicionamos casi nunca. |
| **Coste mal estimado al principio** | Yahoo con 2-4 pb en US100 cuando FTMO cobra 0,5-0,8 pb | Ideas tempranas se descartaron con 3-5 veces el coste real (ya corregido). |
| **Se juzga por R y t, no por lo que cobra la cuenta** | P4 llega tarde | Una regla con asimetría positiva puede valer en FTMO con menos t; otra con t alto pero colas malas no. |

Lo que sí funcionó (ORB US100 y GER40) no salió de un artículo: salió de un **mecanismo** (la apertura de
la sesión propia concentra volatilidad y flujo institucional) explotado con un **pago convexo** (stop corto,
dejar correr al cierre). Varias pruebas fallidas muestran lo mismo de lado: con dirección al azar, stop corto
y salida al cierre dan bruto positivo en ventanas volátiles (GER40 EMA20 +0,10 R, acciones +0,05 R).

## Búsqueda v2: mapa primero, hipótesis después

1. **Atlas condicionado** en lugar de una regla: todas las celdas mercado × ventana de 30 min × horizonte
   × condición conocida al entrar (hueco, día anterior, recorrido desde la apertura, barra previa, nivel de
   VIX, pendiente VIX9D/VIX, día de la semana). Se mide la rentabilidad **en exceso** sobre la misma ventana
   sin condición (la deriva alcista no cuenta como señal).
2. **Filtro estadístico de lote**: Benjamini-Hochberg (FDR 10 %) sobre todas las celdas a la vez, más
   |exceso| ≥ 3 × coste real y mismo signo en ≥ 3 de 4 mercados. Se cuentan **todas** las celdas miradas.
3. **Información nueva antes que reglas nuevas**: VIX y su estructura temporal, amplitud de acciones,
   calendario con sorpresas (MT5 laboratorio), volumen de ticks. Si una idea solo usa el precio del propio
   índice a horas fijas, ya está cubierta por las 25.000 reglas.
4. **Plantilla convexa común** para lo que sobreviva: stop corto en la ventana, salida al final del
   horizonte o al cierre; se juzga directamente por EV/cuota frente al control y por correlación con el ORB.
5. Fuera de muestra 2023-2026 una sola vez, solo para las supervivientes del lote.

Ventaja: un lote de miles de celdas cuesta lo mismo que una idea suelta, cubre los efectos condicionales que
la regla fija diluía y el FDR mantiene honesta la cuenta de pruebas.

## Resultado del primer lote (13-11-2026) y lo que enseña

- **Atlas de dirección** (2.112 celdas, rentabilidad media sin stop): 0 supervivientes; p mínimo 0,006, lo esperable por azar.
- **Atlas convexo** (3.696 celdas, stop 0,15/0,30 ATR y salida al cierre, recorrido M1): 0 supervivientes con BH.
  **Calibración:** la celda del ORB (US100, seguir la primera media hora) sale +0,156 R de exceso sobre
  dirección al azar, t 3,0, neto +0,14 R: el atlas convexo sí ve el ORB; el de dirección no.
  Pero el ORB **no pasa** el FDR ni con solo las 176 celdas sin condición (p 0,003 frente a 0,0006).
- **Lección central:** con 5 años de datos, un edge del tamaño del ORB da t ≈ 3. Cualquier búsqueda masiva
  honesta lo mata. Las búsquedas masivas solo pueden encontrar edges mucho mayores que el ORB, que en
  índices líquidos no existen. Para edges de tamaño ORB hacen falta (a) una hipótesis de mecanismo fijada
  antes (pocas pruebas) o (b) más historia (NQ/ES 2010-2017, Databento) o más mercados con el mismo mecanismo.
- **Patrón de familia:** "seguir el recorrido del día con stop corto hasta el cierre" da exceso positivo en
  casi todas las horas y mercados. Se fija ANTES de abrir 2023-2026 una sola hipótesis: entrada 13:30 NY
  (k = 8) a favor del recorrido desde la apertura, stop 0,15 ATR, salida al cierre; principal US100,
  secundarios US500/US30/US2000 y k = 10, 11.

**Fuera de muestra 2023-2026 (abierto una vez, `orb_acciones/tarde_oos.py`): DESCARTADA.** US100 13:30:
+0,073 R neto en 2018-22 → −0,022 R en 2023-26 (con horquilla FTMO −0,003). Los 12 casos (4 mercados × 3 horas)
son negativos fuera de muestra. Correlación con el ORB baja (0,01-0,16), pero no hay edge que aprovechar.

## Cómo buscar a partir de ahora (cambios al embudo)

1. **Mecanismo antes que datos.** Solo se prueba una idea si se puede decir quién está obligado a operar y
   por qué a esa hora (como la apertura propia del ORB). Nada de anomalías publicadas sin ese porqué.
2. **Pocas pruebas por idea, contadas** (≤ 10). Con 5 años, más pruebas hacen imposible ver un edge de tamaño ORB.
3. **Más historia antes que más reglas:** conseguir NQ/ES/YM 2010-2017 en M1 (crédito gratis de Databento) duplica
   la muestra y permite exigir t ≥ 3 sin matar edges reales.
4. **Medir siempre con pago convexo y contra dirección al azar con las mismas salidas** (el atlas sin stop no ve el ORB).
5. El atlas convexo queda como herramienta de **mapa** (`orb_acciones/atlas_convexo.py`), no de selección.
