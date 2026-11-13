# Plan Darwinex Zero (13-11-2026)

**Objetivo:** un DARWIN en la cuenta de **futuros** de Darwinex Zero con los dos ORB que tienen ventaja
(US100 sobre el NQ y cripto sobre BTC + ETH de CME). Va **además** del plan prop de FTMO, no en su lugar.

**Qué se espera** (media anual de 3 años, cuotas restadas, Monte Carlo 2021-26):

| | Solo DarwinIA SILVER | + GOLD (desde el mes 9) | + permanente 100K (+10 %) | + GOLD + permanente |
|---|---|---|---|---|
| Base | +960 € | +3.600 € | +3.900 € | **+6.550 €** |
| Prudente (costes ×2) | +370 € | +1.800 € | +2.500 € | **+3.900 €** |

Réstale aproximadamente un tercio si el ORB US100 se parece más a 2018-20 que a 2021-26.
El primer año se parece a la columna sin GOLD: GOLD empieza a pagar en el año 2.

**Coste:** unos 52 €/mes (56 $) más 535 € una sola vez por la permanente. Con el plan FTMO
(~120 €/mes de media) suma unos 170 €/mes: dentro del presupuesto de 100-200 €/mes.

---

## Fase 0. Comprobar antes de pagar (hasta el 30-11)

1. Preguntar al soporte de Darwinex Zero, o mirar en la prueba gratuita, estas cuatro cosas:
   - ¿La cuenta de futuros tiene el **BTC (5 BTC)** y el **ETH (50 ETH)** de CME? Los micros (MBT y MET) **no sirven**.
   - ¿Tiene el **NQ** (o MNQ)?
   - ¿Cuánto cobran por contrato? Referencia: hasta unos 15 $ por lado en BTC y ETH sigue siendo rentable.
   - ¿Hay precio anual para la cuenta de futuros?
2. **Si no están BTC y ETH estándar**, el plan B es la cuenta CFD (45 €/mes) con solo el ORB US100 (NDX).
   Rinde menos: +550 €/año solo con SILVER y +3.900 €/año con GOLD y permanente (base).
3. No pagar nada antes de las compras del Black Friday de FTMO (26-29 de noviembre).

## Fase 1. Montar el DARWIN (diciembre, mes 2)

1. Contratar la cuenta de **futuros** en MT5: 1 M$ virtuales, sin pérdida máxima ni swap.
2. Claude escribe dos EAs y los pasa por el Strategy Tester:
   - **ORB_CRIPTO_v100:** rango 9:30-9:40 NY; se opera el lado de la vela si el cuerpo es ≥ 10 % del rango; entrada a las
     9:40; stop 0,15 × ATR14 de la sesión 9:30-16:00; salida a las 15:55; de lunes a viernes; BTC y ETH a igual riesgo.
   - **ORB_US100 v018 para el NQ:** mismas reglas que la cuenta FTMO, con tamaño por contrato de futuro.
   - Cruce con Python: mismo lado ≥ 95 % de los días y R medio ±20 %.
3. **Riesgo:** unos **0,35 % por R y estrategia**. En 1 M$ son unos 3.500 $ por R: ~2 contratos BTC, ~4 ETH y 3-4 NQ.
   Darwinex reescala el riesgo de todas formas. Lo que importa es que las dos estrategias pesen parecido.
4. Pasar la **calibración**: 25 decisiones en ≥ 15 días de trading. Con 3 operaciones al día, unas 2 semanas.

## Fase 2. Primeros 6 meses (enero a junio, meses 3-8)

- **Revisión mensual** junto con la de FTMO: CSV de operaciones de cada EA, R medio por estrategia, rating y ranking.
- **SILVER:** cada mes con rating ≥ 75 entra una asignación de 30.000 € como mínimo, durante 3 meses.
  Se pueden tener varias a la vez.
- **Garantía:** si en los 6 primeros meses no llega ninguna DarwinIA, Darwinex da 25.000 €.
- **Permanente 100K con objetivo +10 % (535 €):** comprarla en el **mes 4-5** si se cumplen dos condiciones:
  - el DARWIN va en positivo desde el inicio;
  - ninguna de las dos estrategias está por debajo de su referencia.
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
| ORB US100 (NQ) | +0,15 R/op con BE a 2R | < +0,10 R tras 100 ops | R medio < 0 tras 100 ops |
| ORB cripto (BTC + ETH) | +0,15-0,20 R/día | BTC y ETH < +0,05 R tras 120 días | R medio < 0 tras 150 días (~7 meses) |

- **Si para el ORB cripto,** se sigue solo con el US100 en la misma cuenta. Cambiar de tipo de cuenta reinicia el DARWIN
  y se pierden las asignaciones.
- **Riesgo principal:** el ORB cripto apenas ganó en BTC en 2025-26; ETH sí. Si se apaga, el DARWIN se queda en lo
  que da el US100 solo.
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
| 1 | nov 2026 | Fase 0: preguntar a Darwinex; compras de FTMO en el Black Friday |
| 2 | dic 2026 | Contratar futuros; EAs, Strategy Tester y calibración |
| 3-5 | ene-mar 2027 | SILVER; revisión mensual; permanente 100K (+10 %) en el mes 4-5 si va bien |
| 6-8 | abr-jun 2027 | Garantía de 25K si no hubo DarwinIA; aplicar las reglas de parada |
| 9+ | jul 2027 | GOLD si cumple; revisión anual en noviembre de 2027 |

Archivos: `INFORME_DARWINEX_ESTRATEGIAS.md`, `proyeccion_salida.txt`, `gold_salida.txt` (en esta carpeta) y
`../darwinex-senales/INFORME_DARWINEX_SENALES.md`.
