# Plan Darwinex Zero (13-11-2026, corregido por la tarde)

> **Corrección (13-11, tarde):** la lista real de futuros de Darwinex Zero **no tiene BTC estándar ni ETH**; solo el micro
> MBT, cuya comisión se come la ventaja. El ORB cripto no es operable en Darwinex (`FUTUROS_DZ.md`). El plan pasa a la
> **cuenta CFD con el ORB US100 solo**. Las cifras de abajo ya están corregidas.

**Objetivo:** un DARWIN en la cuenta **CFD** de Darwinex Zero (45 €/mes, NDX) con el ORB US100 v018. Va **además** del
plan prop de FTMO.

**Qué se espera** (media anual de 3 años, cuotas restadas, Monte Carlo 2021-26, ORB US100 solo):

| | Solo DarwinIA SILVER | + GOLD (desde el mes 9) | + permanente 100K (+10 %) | + GOLD + permanente |
|---|---|---|---|---|
| Base | +550 € | +1.850 € | +2.600 € | **+3.900 €** |
| Prudente (costes ×2) | +200 € | +950 € | +1.600 € | **+2.300 €** |

Réstale aproximadamente un tercio si el ORB US100 se parece más a 2018-20 que a 2021-26.
El primer año se parece a la columna sin GOLD: GOLD empieza a pagar en el año 2.

**Coste:** 45 €/mes (o 420 €/año) más 535 € una sola vez por la permanente.

---

## Fase 0. Antes de pagar (hasta el 30-11)

1. Ya comprobado: NDX en CFD con 0,9 puntos de horquilla y 2,75 $ por orden (coste ≈ FTMO). No hace falta preguntar nada.
2. No pagar nada antes de las compras del Black Friday de FTMO (26-29 de noviembre). Mirar si Darwinex Zero tiene
   oferta de Black Friday en el plan anual.

## Fase 1. Montar el DARWIN (diciembre, mes 2)

1. Contratar la cuenta **CFD** en MT5 (100 K$ virtuales), plan anual si sale más barato.
2. Cargar el **ORB_US100 v018** sobre el símbolo **NDX** (1 lote = 10 × NDX): mismas reglas que en FTMO, gestión de
   fondeada (BE a 2R). Comprobar en el Strategy Tester con el NDX de Darwinex que cuadra con la serie de FTMO.
3. **Riesgo:** ~0,5 % por R. Darwinex reescala el riesgo; basta con que el VaR mensual quede cerca de su banda.
4. Pasar la **calibración**: 25 decisiones en ≥ 15 días de trading (~5-6 semanas con 1 operación al día).

## Fase 2. Primeros 6 meses (enero a junio, meses 3-8)

- **Revisión mensual** junto con la de FTMO: CSV de operaciones del EA, R medio, rating y ranking.
- **SILVER:** cada mes con rating ≥ 75 entra una asignación de 30.000 € como mínimo, durante 3 meses.
  Se pueden tener varias a la vez.
- **Garantía:** si en los 6 primeros meses no llega ninguna DarwinIA, Darwinex da 25.000 €.
- **Permanente 100K con objetivo +10 % (535 €):** comprarla en el **mes 4-5** si se cumplen dos condiciones:
  - el DARWIN va en positivo desde el inicio;
  - el ORB US100 no está por debajo de su referencia.
  Solo se activa cuando el DARWIN sube un 10 % desde la compra.

## Fase 3. GOLD (desde el mes 9, julio de 2027)

- Se entra solo, sin pedirlo, cuando se cumplen tres cosas: más de 8 meses de historial, más de +20 % en el último
  año y rentabilidad/DD por encima de 2,5.
- El ranking es solo por la rentabilidad del mes. En abril de 2026 hubo asignación para 140 de 596 DARWINs:
  69.000 € de media durante 6 meses, y el último premiado ganó +1,63 % ese mes.
- Mientras se está en GOLD no se entra en SILVER. Si se deja de cumplir, se vuelve a SILVER al mes siguiente.
- **No subir el riesgo para escalar.** Darwinex lo reescala igual. Lo que da GOLD es una curva estable.

## Reglas de seguimiento y parada

| Estrategia | Referencia | Alerta | Parada |
|---|---|---|---|
| ORB US100 (NDX) | +0,15 R/op con BE a 2R | < +0,10 R tras 100 ops | R medio < 0 tras 100 ops |

- **Riesgo principal:** es una sola estrategia. Si aparece un segundo sistema con ventaja y correlación ≈ 0, se añade
  al mismo DARWIN (sube el Sharpe y el rating). Cambiar de tipo de cuenta reinicia el DARWIN y se pierden las asignaciones.
- **No reiniciar ni cancelar la suscripción:** se pierde cualquier asignación.

## Otros puntos

- Usar el mismo EA en FTMO y en Darwinex está permitido. FTMO solo sanciona la operativa idéntica por encima de su tope de
  400K, y Darwinex no cuenta para ese tope.
- **Hacienda:** lo más probable es que las comisiones de Darwinex tributen como actividad económica. Hay que consultarlo
  con un asesor antes del primer cobro.
- **Lo que no se va a operar en Darwinex,** porque no tiene ventaja por sí mismo: tendencia y momentum multiactivo, cestas
  siempre compradas (índices, oro, cripto), carry. Detalle en `INFORME_DARWINEX_ESTRATEGIAS.md`.

## Calendario

| Mes | Fecha | Qué |
|---|---|---|
| 1 | nov 2026 | Compras de FTMO en el Black Friday |
| 2 | dic 2026 | Contratar la cuenta CFD; v018 sobre NDX, Strategy Tester y calibración |
| 3-5 | ene-mar 2027 | SILVER; revisión mensual; permanente 100K (+10 %) en el mes 4-5 si va bien |
| 6-8 | abr-jun 2027 | Garantía de 25K si no hubo DarwinIA; aplicar las reglas de parada |
| 9+ | jul 2027 | GOLD si cumple; revisión anual en noviembre de 2027 |

Archivos: `INFORME_DARWINEX_ESTRATEGIAS.md`, `proyeccion_salida.txt`, `gold_salida.txt` (en esta carpeta) y
`../darwinex-senales/INFORME_DARWINEX_SENALES.md`.
