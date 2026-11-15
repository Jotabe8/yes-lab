# Revisión 2 de descartados con el motor actualizado · preregistro (14-11-2026, antes de correr nada)

Jorge pide otra tanda de revisión de los descartados ahora que el embudo tiene la prueba de paseo aleatorio en P1
(`metodo/sinteticos.py`), la comparación operación a operación en P5 y el revisor de código contra preregistro.

Punto de partida: la revisión 1 (PR #30, rama `claude/project-thread-gpiyvs`) ya re-probó con historia larga lo
que el triaje dejaba (gotobi y EIA) y no revivió nada. Las pruebas nuevas sirven sobre todo para cazar **falsos
positivos** (ventaja fabricada por el motor). Un descarte injusto solo puede venir de un motor con **sesgo
negativo** (regla pesimista en velas ambiguas, stop mal recorrido, hueco mal tratado, coste u hora mal puestos).
Así que esta revisión busca eso y nada más. No se re-optimiza ni se añaden variantes.

## A. Prueba del motor (paseo aleatorio) en los casi-positivos

Mismo código de backtest que dio el veredicto, sin cambiar ni una regla, corrido sobre `velas_paseo` (velas
reales barajadas entre días dentro de cada minuto del día y centradas: no hay nada que ganar).

| Caso | Código del veredicto | Datos | Réplicas |
|---|---|---|---|
| Gotobi USDJPY (comprar 08:00→09:55 JST) | `metodo/revision/analisis.py` (PR #30) | M1 medio Dukascopy 2003-26 de PR #30 | 20 por año |
| Deriva EIA USOIL (miércoles 10:35→14:30 NY) | ídem | M1 medio 2011-26 de PR #30 | 20 por año |
| ORB GER40 (vela 9:00-9:10 Fráncfort, stop 0,15 ATR) | `metodo/v3/orb_ger40.py` | M1 bid/ask Dukascopy 2013-26 (workflow) | 20 por año |
| ORB JP225 (vela 9:00-9:30 Tokio, stop 0,15 ATR) | `metodo/v3/orb_asia.py` | M1 bid/ask Dukascopy 2018-26 (workflow) | 20 por año |
| Ciclo de subastas del Tesoro (IEF diario) | `metodo/v4/subastas.py` | IEF diario de `metodo/v4/datos` | 200 (barajado de días) |

El barajado se hace **dentro de cada año** para que el nivel de precio no se aleje del real. En gotobi y EIA las
velas son solo las de la ventana de la operación (así se guardaron en PR #30); el ATR o el rango diario siguen
siendo los reales, lo que cambia la escala de R pero no su media.

Métrica: R bruta media de todas las operaciones de todas las réplicas, su t (`sinteticos.prueba_motor`) y el
sesgo en múltiplos del coste del lugar.

**Lectura (fijada antes):**
- |t| < 2 → el motor está limpio. El veredicto de descarte se mantiene tal cual (la ventaja bruta era real y lo
  que la mató fue el coste o la potencia, no el motor).
- t ≤ −2 (sesgo negativo) → hay un fallo que escondía ventaja. Se busca el fallo en el código, se corrige (no se
  resta el sesgo) y se repite **una vez** la prueba original con su regla preregistrada. Revive solo si: t neto
  ≥ 2,4 con toda la historia (2,64 si son dos re-pruebas, 2,75 si tres), costes ×2 > 0, segunda mitad > 0 y
  supera su placebo.
- t ≥ 2 (sesgo positivo) → la ventaja bruta era en parte del motor; el caso pasa a clase E en el registro.

## B. Auditoría de código de los descartes con bruto > 0 (clases B y D)

Lectura del código que dio cada veredicto buscando los cuatro fallos que este proyecto ya ha visto:
(1) stop no recorrido vela a vela o recortado a −1; (2) hueco no llenado a la apertura de la vela; (3) coste mal
puesto (horquilla Dukascopy de Asia, que exagera 1,6-1,9×, o coste supuesto en vez de medido); (4) hora mal
puesta (cambio de horario, hora de servidor fija, cierre de sesión). Solo se reabre lo que tenga un fallo
**confirmado en el código** que pueda haber hundido el resultado y cuyo arreglo no esté ya hecho; mismo listón que
en A. Lo que esté arreglado en una prueba posterior o no tenga fallo se deja como está.

Casos: los 11 de clase B y los 10 de clase D de `metodo/v3/registro_ideas.csv`.

## C. Lo que no se hace

- Víspera de festivo: tenía un coste supuesto 3-5× el real y aperturas rancias de Yahoo (dos fallos de datos que
  empujan en sentidos contrarios), pero T0 dice que no es medible con ninguna historia (~9 fechas/año, 6 pb con
  σ ≈ 100 pb: harían falta más de 100 años). Arreglar el coste no cambia eso. Se deja.
- Nada de otros stops, otras horas, filtros ni mercados nuevos.
