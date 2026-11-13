# Preregistro v3 · ORB GER40 con el coste real de FTMO (13-11-2026, antes de ver los datos nuevos)

**Por qué (T1):** familia de volatilidad en apertura propia, la única con éxitos. El ORB GER40 se aparcó porque
la referencia 2022-26 daba +0,096 R con un spread supuesto. La horquilla real de FTMO en la primera hora de Xetra
es 0,0052 % (medida en el MT5, sep-nov 2026), menor que la supuesta. Jorge pidió repetir la prueba (13-11).

**T0:** bruto conocido ~0,17 R (distinta-orb 2018-22); coste 0,0052 % × 24.000 / (0,15 × ATR ≈ 50 pts) ≈ 0,025 R →
margen bruto/coste ≈ 7 (en pb: ~15 pb de bruto frente a 0,5 pb). ~240 ops/año; con neto 0,12 R y σ 1,8
hacen falta ((3,24 × 1,8 / 0,12)² / 240) ≈ 9,8 años; hay 14,8 (2012-01 → 2026-11). Pasa T0.

**Regla (la del EA ORB_GER40_v100, sin cambios):** hora de Fráncfort. Rango de apertura 9:00-9:10; dirección del
cuerpo de ese rango (≥ 10 % del rango, si no, no opera); entrada a la apertura de las 9:10; stop 0,15 × ATR(14)
diario (días del servidor FTMO = NY + 7 h); sin objetivo; salida a las 17:25. Una operación al día.
Simulación en M1 de Dukascopy (deuidxeur) en **precio medio**; stop vela a vela, huecos a la apertura de la vela.
**Coste:** 0,0052 % del precio de entrada por operación (horquilla FTMO, índices sin comisión).

**Variantes (3 en total):**
1. **Principal:** R puro (salida 17:25), 2012-01 → 2026-11.
2. Fondeada: stop a entrada al ganar 2 R (como el .set de la fondeada).
3. Costes ×2 sobre la principal.

**Pasa si:** t neto ≥ 2,4; segunda mitad (2019-07 → 2026-11) > 0; costes ×2 > 0; supera al **placebo de lado**
(lado contrario, mismas salidas) y al **placebo de hora** (misma regla con rango 11:00-11:10).
Correlación diaria con el ORB US100 v018 < 0,3. Comprobación de réplica: mismo lado que la referencia Python
2022-26 (ORB_GER40_referencia_python.csv) en ≥ 95 % de los días comunes.
Si falla: clase B o D en el registro, sin rescates. Si pasa: vuelve a la ruta (Jorge decide).
