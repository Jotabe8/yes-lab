# Revisión de descartados · triaje y preregistro (14-11-2026, antes de descargar datos nuevos)

Jorge pregunta si algún descartado antiguo podría funcionar con el proceso refinado. La auditoría de hoy
(`metodo/combinar/INFORME.md`, PR #27) dio dos motivos legítimos para reabrir: (a) muchas pruebas se decidieron
con 5 años, que no bastan para ver un edge del tamaño del ORB; (b) 12 ideas se descartaron por "no medible", no
por evidencia. Riesgo opuesto: re-probar lo que ya se ha visto hasta que algo salga. Por eso: triaje con reglas
fijas, **como mucho 2 re-pruebas**, listón corregido por esas 2, y la decisión se apoya en el **tramo de historia
que nunca se miró**.

## 1. Triaje (registro `metodo/v3/registro_ideas.csv`, 72 familias)

Se reabre solo si se cumplen las tres:

1. Tenía **bruto claro** (t bruto ≥ 2 o bruto > coste) — fuera las 40 clase A.
2. El veredicto salió de una **ventana corta** (≤ 9 años) **o** de un **coste mal medido**, no de una prueba con
   historia larga ni de un problema de lugar/regla que la historia no arregla.
3. **Existe historia no mirada** que da potencia suficiente (T0: años necesarios ≤ años disponibles).

| Candidata | Bruto previo | Ventana del veredicto | ¿Qué la mató? | ¿Reabrir? |
|---|---|---|---|---|
| **Gotobi yen** | +0,106 R t 3,5 USDJPY; EURJPY/GBPJPY t 4,8-5,0 | 2018-26 (9 años) | Coste: bruto 1,5× coste (con horquilla Dukascopy, que en Asia exagera 1,6-1,9× según v3) | **Sí**: 2003-08 → 2017 sin mirar (14 años) |
| **Inventario EIA petróleo** | +33 pb t 2,1 (2021-22) | 2021-26 (6 años) | Se apagó en 2023-26 (+11 pb t 1,1) | **Sí**: USOIL M1 desde 2011-09 sin mirar (9 años) |
| ORB GER40 | +0,098 R t 2,2 | **2012-26 ya** (v3) | t neto 1,58 con 14 años | No: ya tuvo historia larga |
| Prima nocturna US | t 2,36 | **2011-26 ya** (futuros CME) | Sharpe < siempre comprado; swap en CFD | No: historia larga + regla |
| ORB cripto 9:30 NY | +0,195 R t 3,0 | 2021-26 | **Lugar**: no hay BTC/ETH a ≤ 0,02 % i/v que quepa en una prop | No: más historia no cambia el coste. Disparador sigue: lugar barato |
| Carry cripto | t 18 | 2019-26 | Exceso sobre letras ≈ 0 desde 2025 (se agotó) | No: el problema es el presente, no la potencia |
| Víspera de festivo | +0,044 R, 12/13 índices | **2000-22 ya** | Coste supuesto 3-5× el real, pero T0: ~10 fechas/año comunes a todos los índices, efecto 6 pb con σ diaria ~100 pb → harían falta >300 años; además usaba aperturas de contado de Yahoo (rancias) | No: no medible con ninguna historia (clase C real) |
| Zona de ruido US100 | +0,10 R | 2018-26 | Se apaga + colas −7 R; es momento intradía US100 (misma información que el ORB) | No: el atlas 2012-22 no vio nada nuevo en esa familia |
| Tendencia de tarde convexa | +0,07 R | 2018-22 | ya re-probada con 2012-22 en el atlas largo | No |
| GER40 EMA20 M30 | +0,19 R | 2022-26 | No se repite en 14 mercados | No: falló la réplica, no la potencia |
| ORB JP225 / Asia | bruto t 3,3 | 2018-26 | Coste FTMO 0,09 R (horquilla medida) | No: lugar |
| Resto clase C (T0 > 30 años, datos no accesibles) | — | — | No medibles | No |

**Re-pruebas: 2 (gotobi y EIA).** Listón corregido: el t ≥ 2,4 de una prueba única (p ≈ 0,008 a una cola) pasa a
**t ≥ 2,64** (Bonferroni para 2). Las dos ya se vieron en parte, así que además se exige que el **tramo nunca
visto** pase por sí solo.

T0 aproximado (σ por operación ≈ 0,7-0,8 R con estos stops):
- Gotobi: bruto ~0,10 R → medible en ~7 años; el **neto** depende del coste: con 1,6 pips (0,07 R) harían falta
  >60 años; con ≤ 1 pip, ~20 años (hay 23). Lo que esta prueba sí puede decidir: si el bruto se replica en 14
  años nuevos y qué coste máximo aguanta.
- EIA: con neto 0,10 R y ~50 ops/año, ~13 años (hay 15). Con 0,05 R no es medible.

## 2. Gotobi en el yen (re-prueba 1)

Regla (la misma de 2026-10-26, sin cambios): días gotobi = 5, 10, 15, 20, 25 y último del mes; si caen en sábado
o domingo, el viernes anterior. **Comprar** a la apertura de la vela M1 de las 08:00 JST (23:00 UTC del día
anterior) y cerrar al cierre de la vela de las 09:54 JST (09:55). Stop = 0,25 × media de 14 días del rango
diario (H−L) de los días de servidor (NY 17:00) anteriores; stop vela a vela, hueco a la apertura de la vela.
Precio **medio** de Dukascopy (bid+ask)/2.

- Mercado que decide: **USDJPY**. EURJPY y GBPJPY: réplica.
- **Coste que decide** (lugar de hoy): mediana 2023-26 de la horquilla Dukascopy a las 08:00 JST en % del precio
  + comisión 0,005 % del nominal ida y vuelta (5 $ por lote de 100k), aplicada a todos los años. Informativo:
  horquilla histórica de cada día; coste de equilibrio en pips.
- Placebo: la misma regla en días **no gotobi** a la misma hora; p95 de 2.000 muestras del mismo tamaño.

**Pasa si (todas):** t neto USDJPY 2003-26 ≥ 2,64; tramo nunca visto (2003-08 → 2017-12) bruto t ≥ 2 y neto > 0;
tramo 2018-26 neto > 0; costes ×2 neto > 0; bruto > p95 del placebo; al menos uno de EURJPY/GBPJPY con bruto
t ≥ 2 en el tramo nunca visto.

## 3. Deriva tras el inventario EIA (re-prueba 2)

Regla (la B2 congelada el 30-10 con stop 0,5 ATR, sin cambios): miércoles; dirección del movimiento entre la
apertura de la vela de las 10:30 NY y el cierre de la de las 10:34; entrar al cierre de las 10:34 a favor; salir
al cierre de la vela de las 14:29 NY. Stop 0,5 × ATR(14) diario (true range, días de servidor NY 17:00, conocido
antes del día), vela a vela. USOIL = `lightcmdusd` de Dukascopy, precio medio.

- **Coste que decide:** 5,3 pb del precio por operación (horquilla FTMO medida en 2023-26). Informativo: horquilla
  Dukascopy del día.
- Placebos: dirección al azar con las mismas entradas y salidas (p95 de 2.000) y la misma regla los lunes,
  martes, jueves y viernes (el miércoles debe superar a los cuatro).

**Pasa si (todas):** t neto 2011-09 → 2026-11 ≥ 2,64; tramo nunca visto (2011-09 → 2020-12) bruto t ≥ 2 y neto > 0;
tramo 2021-26 neto > 0; costes ×2 > 0; > p95 del placebo de dirección y > los otros cuatro días.

## 4. Qué pasa después

- No pasa: se anota en el registro con su motivo; no hay más variantes (ni otro stop, ni otra hora, ni filtros).
- Pasa: no va al dinero directamente (regla de la auditoría v4): coste real en el lugar (horquilla FTMO medida en
  MT5 a esa hora), reserva hacia delante en papel y después MQL5 + Strategy Tester. Jorge decide.
