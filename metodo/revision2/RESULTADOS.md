# Revisión 2 de descartados con el motor actualizado: resultados (14-11-2026)

Preregistro `PREREGISTRO.md` y scripts subidos **antes** de correr nada (commit `d79e77f`). Salidas:
`paseo_local_salida.txt` (gotobi, EIA, subastas, en la nube con los datos de PR #30) y `paseo_orb_salida.txt`
(ORB GER40 y JP225, datos bajados en GitHub Actions, `paseo/*.csv.gz`).

**Veredicto: no revive ninguna.** Los motores que dieron los veredictos están limpios: sobre velas de paseo
aleatorio dan R ≈ 0. Así que la ventaja bruta que tenían los casi-positivos era real, y lo que los mató (el coste
del lugar o la falta de potencia) sigue en pie. Ningún descarte se debió a un fallo del motor.

## A. Paseo aleatorio en los casi-positivos

El mismo código de cada veredicto, sin tocar una regla, sobre velas reales barajadas entre días dentro de cada
minuto del día (hora local) y centradas. Primero se comprobó que, con los datos reales, cada script reproduce el
número del veredicto original (sí, al decimal).

| Caso | Bruto real | Neto real (veredicto) | Paseo: R bruta media | t | Ops del paseo | Sesgo / coste | Motor |
|---|---|---|---|---|---|---|---|
| Gotobi USDJPY 2003-26 | +0,110 | t 1,56 | +0,016 | 1,71 | 33.820 | 0,20× | limpio |
| Deriva EIA USOIL 2011-26 | +0,045 | t 0,05 | −0,007 | −0,93 | 15.180 | 0,17× | limpio |
| ORB GER40 2013-26 | +0,098 (t 2,24) | t 1,58 | −0,001 | −0,16 | 60.852 | 0,0× | limpio |
| ORB JP225 2018-26 | +0,166 (t 3,26) | t 1,50 | +0,017 | 1,81 | 41.544 | 0,2× | limpio |
| Subastas del Tesoro IEF | +4,2 %/año | t 2,62 (D: inestable) | +0,1 %/año | 1,22 | 200 barajados | — | limpio |

- Ningún motor tiene sesgo **negativo**: no había ventaja escondida que una simulación pesimista hubiera hundido.
  Ese era el único camino por el que esta revisión podía revivir algo.
- Gotobi y JP225 dan un sesgo positivo pequeño (+0,016 y +0,017 R, t < 2). Si fuera real, su ventaja sería algo
  **menor**, no mayor. Lo más probable es ruido: las 20 réplicas reutilizan las mismas velas.
- Observación: en el ORB GER40 la operación del lado contrario (el placebo de v3) da +0,025 R con t 2,89 en el
  paseo. Eso infla el placebo, no la regla, así que hacía más difícil pasar, no más fácil. El veredicto de GER40
  salió del t neto de la regla (1,58), cuyo motor da −0,001. No cambia nada.

## B. Auditoría de código de los descartes con bruto > 0 (clases B y D)

Se leyó el código de cada veredicto buscando los cuatro fallos ya vistos (stop sin recorrer o recortado a −1,
hueco sin llenar a la apertura, coste mal puesto, hora mal puesta).

| Caso | Fallo encontrado | ¿Pudo hundir el resultado? |
|---|---|---|
| ORB acciones en juego | **Sí**: en la vela de entrada (orden stop dentro de la vela), si el mínimo toca el stop se cuenta como stop aunque pudo ocurrir antes de entrar (`orb_acciones/procesar.py`, regla "conservadora") | **No.** El placebo de dirección aleatoria usa las mismas entradas con la misma regla, así que el sesgo es común y la regla ya estaba por debajo del p95 del placebo (+0,061 frente a +0,097). Además el coste (0,11 R stop B; 0,49 R stop A) supera cualquier sesgo plausible. |
| ORB cripto | Stop en bid con horquillas Dukascopy (artefacto) | Ya arreglado en v3 (precio medio) y cerrado en v6 por la réplica en 8 monedas. |
| ORB JP225 / Asia, gotobi | Horquilla Dukascopy de Asia exagerada | Ya arreglado: horquilla FTMO medida en MT5 (JP225 0,0157 %, gotobi 1,52 pips). |
| Prima nocturna tras estrés, NR7 | `max(R, −1)` y precios rancios de Yahoo | Fallos que **fabricaban** ventaja; ya corregidos (clase E). |
| Scalping NNFX, GER40 EMA20 | Si en un minuto tocan stop y objetivo, cuenta el stop | Minuto a minuto y con placebo aleatorio con el mismo motor: el sesgo es común y no cambia la comparación. |
| ORB GER40, zona de ruido, tendencia de tarde, variantes y filtro del ORB, deriva nocturna, EIA | Ninguno: entrada a la apertura de una vela, stop vela a vela con hueco a la apertura, zona horaria local con cambio de horario | — |
| Prima nocturna, fin de mes FX, rebalanceo 60/40, VX, carry y financiación cripto, subastas, cambio de año | Motores diarios sin stop dentro de la vela | Nada que recorrer; el rebalanceo y la zona de ruido además se repitieron en v8. |

La única regla pesimista del proyecto (ORB acciones) no pudo esconder ventaja por cómo se juzgó. No hay re-pruebas.

## C. Lo que queda

- Nada se reabre. Los disparadores que ya existían no cambian: gotobi solo con coste total ≤ 0,8 pips a las
  08:00 JST (FTMO midió 1,52); JP225 solo con horquilla ≤ 0,005 %.
- Lección para el método: el paseo aleatorio confirma que los motores del proyecto desde v3 son fiables, también
  hacia abajo. Los descartes de este registro no son injustos: les falta señal o les sobra coste.
- Víspera de festivo no se re-probó (no es medible con ninguna historia, ver preregistro).
