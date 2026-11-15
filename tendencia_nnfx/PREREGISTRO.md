# Preregistro: tendencia de largo plazo en forex con gestión NNFX (14-11-2026)

Escrito y subido **antes** de ejecutar ninguna simulación de la estrategia. Solo se revisó la calidad de los
datos (fechas, huecos, máximos y mínimos coherentes).

## Hipótesis y mecanismo

Las divisas tienen tendencias de meses por política monetaria divergente y por flujos lentos (bancos centrales,
coberturas corporativas) que no buscan beneficio a corto plazo. Es la prima de "time-series momentum" publicada
(Moskowitz, Ooi y Pedersen 2012; Menkhoff et al. 2012). Se sabe que se ha debilitado desde ~2010 en forex. La
pregunta es si, con la gestión NNFX y los costes y el swap de un CFD prop, queda algo.

## Datos

- D1 de MT5 en `data/ohlc` del PC (copiados a `tendencia_nnfx/datos/`), 11 pares: AUDNZD, AUDUSD, EURAUD,
  EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY. Marzo 2005 → mayo 2026 (~21 años).
- Oro fuera (no es forex y su D1 tiene 25 velas con máximo/mínimo incoherente).
- Tipos a 3 meses de la OCDE (FRED, mensuales) para el swap: EZ, US, GB, JP, AU, NZ, CA, CH.

## Reglas (fijas, sin optimizar)

**Señal de entrada** (al cierre del día t; entrada a la apertura de t+1). Tres variantes, la primera decide:

- **V1 (principal): Donchian 55.** Cierre > máximo de los 55 días anteriores → largo; cierre < mínimo → corto.
- V2: Donchian 100 (más lenta).
- V3: cruce de medias simples 50/200 (largo cuando la SMA50 cruza por encima de la SMA200, corto al revés).

Una posición por par; no se abre otra mientras quede alguna mitad abierta.

**Gestión NNFX** (igual en las tres):

- ATR(14) de Wilder al cierre de la señal. Stop inicial a 1,5 ATR de la entrada. Riesgo total 1 R.
- Dos mitades de 0,5 R. Mitad A: objetivo a 1 ATR. Mitad B: sin objetivo.
- Al tocar el objetivo de A, el stop de B pasa a la entrada (BE).
- Salida por indicador de B (y de A si sigue abierta): cierre que rompe el canal contrario de la mitad de
  longitud (Donchian 27 en V1, 50 en V2; en V3 el cruce contrario de medias). Se sale a la apertura siguiente.
- Vela a vela con máximo/mínimo diario. Si en la misma vela caben stop y objetivo, **cuenta el stop**. Huecos
  a la apertura: se llena a la apertura.

**Costes (ida y vuelta, en pips, spread + comisión FTMO):** EURUSD 0,8; USDJPY 0,9; AUDUSD 1,0; GBPUSD 1,1;
USDCAD 1,3; USDCHF 1,3; NZDUSD 1,4; EURJPY 1,5; EURAUD 2,0; GBPJPY 2,5; AUDNZD 2,5. Prueba de estrés ×2.

**Swap:** por noche = dirección × (tipo de la base − tipo de la cotizada) / 365 × precio − recargo 1,5 %/año
× precio, por cada día natural en posición (incluye fines de semana). En R: dividido por la distancia del stop.
Estrés: recargo 3 %/año.

## Placebos (200 réplicas)

1. **Entrada aleatoria:** mismo nº de entradas por par, en días al azar, dirección al azar, misma gestión y
   salida (el canal contrario se mide respecto al lado aleatorio).
2. **Lado contrario:** misma señal, dirección opuesta, misma gestión.

## Criterio (T4 de la búsqueda v3), sobre V1, toda la historia agrupada

Pasa solo si se cumplen todos:

1. R neta media (costes 1× y swap) con **t ≥ 2,4**.
2. Segunda mitad (2016-2026) con R neta media > 0.
3. Costes ×2 y recargo de swap 3 % → R neta media > 0.
4. R neta media por encima del **p95** del placebo de entrada aleatoria.
5. ≥ 7 de 11 pares con R neta > 0.

V2 y V3 se informan; solo podrían sustituir a V1 cumpliendo lo mismo (con 3 variantes, aviso de multiplicidad).
Si pasa: P4 (EV por cuota 2-Step frente al control) y después MQL5. Si no pasa: descartada, sin capas extra.
