# Preregistro: estrategias para Darwinex Zero (13-11-2026)

Escrito antes de ejecutar las pruebas B y C. Proceso v3 (`metodo/BUSQUEDA_V3.md`).

## Qué cambia en Darwinex Zero (DZ)
- Sin pérdida máxima ni diaria; cuenta de futuros (CME/Eurex vía Interactive Brokers) con 1 M$ virtuales,
  cuenta CFD con 100 K$. Futuros: sin swap (la financiación va implícita en el precio).
- Se cobra por nota (67 % retorno 6 meses, 22 % mes en curso, 11 % DD) sobre el DARWIN reescalado a VaR
  objetivo: lo que cuenta es el retorno por unidad de riesgo (Sharpe) y la estabilidad en ventanas de 6 meses.

## A. ORB cripto 9:30 NY en futuros CME estándar (reapertura de una clase B por lugar)
Sin prueba nueva: la prueba preregistrada (commit c974bce) ya pasó con costes de contrato estándar CME
(t 2,98). El disparador anotado era "cuenta de futuros con pérdida máxima ≥ 15.000 $": DZ futuros no tiene
pérdida máxima y 1 contrato BTC (~1.800 $ de riesgo) es el 0,18 % de 1 M$. Solo se recalculan métricas
de DARWIN (Sharpe mensual, ventanas de 6 meses, correlación con el ORB US100). Requisito para seguir:
que DZ liste los contratos BTC (5 BTC) y ETH (50 ETH) de CME.

## B. Momentum de series temporales multiactivo (una sola especificación)
- Mercados: índices (US500, US100, US30, US2000, GER40, FRA40, EU50, UK100, JP225, AUS200, HK50), forex
  (pares de datos_tendencia), metales (XAU, XAG, XPT). Sin energía ni agrícolas (series continuas de Yahoo
  sin ajustar el vencimiento).
- Rentabilidad tipo futuro: índices precio − tipo a 3 m de su divisa + dividendo fijo (EE. UU. 1,8 %, Europa
  3 %, UK 3,5 %, Japón 1,8 %, AUS 4 %, HK 3 %); forex spot + diferencial de tipos; metales spot − tipo USD.
- Señal: signo de la rentabilidad de 12 meses (252 días), revisión al cierre de cada mes. Peso de cada
  mercado = 10 % / vol EWMA 60 días anualizada, dividido por nº de mercados activos; cartera reescalada
  a 10 % de vol objetivo con la vol realizada de 12 meses de la propia cartera (sin mirar adelante).
- Coste: 2 pb por cada unidad de nocional movida + 0,2 %/año de rolls.
- Periodo: 2005-01 → 2026-10 completo (sin ajuste/OOS, ≤ 1 variante).
- Pasa si: t neto ≥ 2,4 (SR ≥ 0,51 en 22 años); 2ª mitad > 0; costes ×2 > 0; y supera al placebo
  (misma cartera siempre comprada con las mismas ponderaciones) en exceso con t ≥ 2.

## C. Cesta de primas siempre comprada (índices + oro, vol 10 %)
Misma construcción que B con señal = +1 siempre. Es beta, no ventaja: no puede pasar por sí misma
(regla de Jorge). Solo se mide si mejora el DARWIN del ORB US100: se descarta salvo SR 2005-26 ≥ 0,5 y
subida del Sharpe mensual del ORB 2018-26 ≥ 0,10 al mezclarla a igual riesgo.
