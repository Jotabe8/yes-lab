# Búsqueda v4: auditoría del proceso y búsqueda sin restricciones (13-11-2026)

Pedido de Jorge: buscar fallos en el sistema de búsqueda y creación de estrategias, crear un sistema nuevo y con él
una estrategia con ventaja en cualquier mercado, sin tener en cuenta reglas de firmas, brókers ni regulación (sí
dentro de la ley: nada de manipulación ni información privilegiada). Si no sale positivo, repetir.

## Resultado en una línea

**Ninguna de las 10 estrategias pasa su prueba preregistrada.** Dos ventajas son reales pero no sirven hoy: el carry
de financiación cripto (pasa todo, se replica en 126 monedas no vistas, pero desde 2025 rinde menos que las letras del
Tesoro) y el ciclo de subastas del Tesoro (pasa t, placebo y réplica en el futuro ZN, pero su caída máxima es 4,6
veces su beneficio anual y desde 2016 da ≈ +1 %/año). El ORB US100 sigue siendo el único sistema.

## Parte 1: fallos encontrados (detalle en `AUDITORIA.md`)

| # | Fallo | Gravedad | Qué se hizo |
|---|---|---|---|
| 1 | La regla de parada en real (R < 0 tras 100 ops) mata un ORB bueno el 25 % de las veces y deja vivo uno muerto el 49 % | Alta | Propuesta: cruce diario real vs réplica + prueba secuencial de Wald |
| 2 | Todo el universo de búsqueda estaba recortado por FTMO (ninguna prima de riesgo probada) | Alta | Origen de la v4 |
| 3 | Preregistros sobre datos ya vistos; ~63 familias → se esperan 0,6-1,3 falsos positivos en el proyecto | Media-alta | Regla: réplica en instrumento/periodo no mirado o reserva hacia delante |
| 4 | Deflated Sharpe mezclaba Sharpe por operación con varianza diaria (listón √k más bajo) | Media | **Corregido** en `embudo.py` |
| 5 | Sesgo de supervivencia en el universo de acciones | Media | Anotado |
| 6 | Sin placebo para estrategias de exposición continua | Media | Placebo de rotación temporal |
| 7 | Simulador FTMO con días independientes | Baja | Medido: no cambia el ORB |
| 8 | Deslizamiento del stop en real | Ninguna | 8 stops reales: −0,99 R de media |

## Parte 2: el sistema nuevo (v4, "búsqueda por pagador")

1. Antes de mirar datos se escribe **quién paga y por qué seguirá pagando** (asegurados, apalancados, emisores, índices,
   vendedores por impuestos...). Sin pagador identificable, la idea no entra.
2. Se prueba en el **instrumento real** con su coste real (futuros, ETF, perpetuos), no en un CFD.
3. **Preregistro en el repositorio antes de descargar** (`PREREGISTRO_V4*.md`): una variante principal y como mucho dos
   informativas, señal con un día de retraso, listón t neto ≥ 2,4, 2ª mitad > 0, costes ×2 > 0, placebo (rotación de
   la exposición o selección al azar) p95, y **regla de cola: caída máxima a vol 15 % < 3 × beneficio anual**.
4. **Réplica obligatoria** en un instrumento, universo o periodo que no se haya mirado.
5. Si pasa, reserva hacia delante antes de dinero real. Si no pasa, no se rescata con variantes elegidas después.

## Las 10 pruebas

| # | Estrategia (pagador) | Datos | Resultado | Veredicto |
|---|---|---|---|---|
| 1 | Prima de volatilidad: corto VIX en contango (compradores de seguro) | Futuros VX 2013-26, VXX/SVXY | +14,8 %/año t 0,79, DD 12× beneficio; −127 % en feb-2018 | No pasa |
| 2 | Carry de financiación cripto: contado largo / perpetuo corto (apalancados largos) | Binance, 20 monedas 2020-26 | t 18, pero exceso sobre letras: 2020-21 +19/+38 %, 2025 −0,5 %, últimos 12 meses +0,1 % | Pasa el preregistro; **agotado** |
| 3 | Financiación transversal (largo financiación baja / corto alta) | Mismas 20 | +19 %/año t 2,38 (listón 2,4), 2ª mitad +8 % | No pasa |
| 4 | ETF 3x por pares (decaimiento por volatilidad; los que compran apalancado) | 12 pares 2012-26 | ≈ 0 salvo un artefacto de precios de Yahoo (ERY 2020) | No pasa |
| 5 | Reversión semanal cripto (provisión de liquidez) | 20 monedas | −17 %/año t −1,8 | No pasa |
| 6 | Momentum transversal cripto, universo no visto | 131 perpetuos | +4 %/año t 0,29, bajo placebo; réplica del carry: exceso +8,8 % t 2,55 pero 2026 −17 % | No pasa |
| 7 | Corto de perpetuos recién listados frente a BTC (compradores de novedad) | 877 listados 2020-26 | +0,12 %/día t 2,23; mediana por listado +4,9 %, pero un listado perdió −494 % | No pasa (cola de ruina) |
| 8 | Ciclo de subastas del Tesoro (creadores de mercado primarios) | IEF 2002-26 + 1.588 subastas | +3,3 %/año t 2,62, placebo y ZN t 3,5 pasan; DD 4,6× beneficio; 2016-26 +1 %/año t < 0,5 | No pasa (cola y se apaga) |
| 9 | Apostar contra la beta (inversores sin apalancamiento) | 9 ETF sectoriales 1999-26, 20 de país | +0,9 %/año t 0,25; países −1,5 % | No pasa |
| 10 | Cambio de año en pequeñas (venta por pérdidas fiscales) | IWM−SPY 2000-26, ^RUT 1988-99 | 2000-25 −0,3 % por invierno t −0,8; 1988-99 +2,0 % t 3,3 | No pasa (murió tras publicarse) |

## Qué se aprende

- **Las primas con pagador sí existen, pero o se cobran con colas que arruinan (volatilidad, listados) o se agotan en
  cuanto se popularizan** (carry cripto desde 2025, enero desde 2000, subastas desde 2016). Es el patrón de la
  literatura: el efecto publicado se reduce a la mitad o desaparece tras publicarse.
- Quitar las restricciones de FTMO no cambia el resultado: el cuello de botella no eran las reglas sino que el dinero
  fácil ya lo cobra alguien con menos coste.
- Dos datos curiosos que **no** son estrategia (no se dejan en reserva, regla de Jorge): todo el rendimiento del bono
  a 10 años de 2002-2026 se concentra en los 4 días posteriores a las subastas (el resto de días −0,2 %/año), y el
  corto de listados gana en el 62 % de los casos.
- Disparadores para reabrir: carry cripto si la financiación media de 30 días vuelve a > 0,03 %/8 h (≈ 33 %/año) con
  letras < 3 %; subastas si 2027 con datos nuevos da > +3 %/año en ZN con la misma regla (prueba única, sin cambios).

## Archivos

Todo en `metodo/v4/`: auditoría y scripts (`auditoria/`), preregistros `PREREGISTRO_V4*.md`, descargas
(`descargar_*.py` + workflows `v4-*.yml`), análisis `*.py` con su salida `*_salida.txt` y series diarias `*_diaria.csv`.
