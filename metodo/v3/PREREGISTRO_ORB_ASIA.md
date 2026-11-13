# Preregistro v3 · ORB de la apertura propia en Asia, agrupado (13-11-2026, antes de ver datos nuevos)

**Por qué (T1):** familia de volatilidad en apertura propia, la única con éxitos (ORB US100, GER40). En la prueba
de horarios (distinta-orb, 2018-22) JP225 en Tokio tuvo bruto +0,159 R y superó al placebo, pero se descartó
por un coste de 0,126 R **medido con la horquilla de Dukascopy, no con la de FTMO** (en BTC Dukascopy exageraba ×20).
Además aquella prueba fijaba la barra de Tokio a las 02:00 del servidor: de marzo a noviembre eso es las 8:00 JST,
una hora antes de la apertura. Error de horario (clase E) que pudo esconder parte del efecto.

**T0:** JP225 solo: bruto 0,159, ~220 ops/año → con neto 0,12 R harían falta ~11 años (hay 8,8): no pasa solo.
Agrupando el mismo mecanismo en 2-3 mercados asiáticos (JP225, HK50, AUS200) la potencia sube a >80 %. Pasa T0.
Oro en NY (bruto 0,139, 1 mercado): ~12 años necesarios → fuera en T0, no se prueba.

**Regla (la del ORB en barras de 30 min, sin cambios):** primera barra de 30 min desde la apertura de contado
**en hora local** (JP225 9:00 JST, HK50 9:30 HKT, AUS200 10:00 hora de Sídney); dirección del cuerpo (≥ 10 % del
rango); entrada al cierre de esa barra; stop 0,15 × ATR(14) de los rangos diarios de sesión; sin objetivo; salida
al cierre de contado local (JP225 15:00, 15:30 desde 05-11-2024; HK50 16:00; AUS200 16:00). Stop vela a vela en M1
sobre **precio medio**; huecos al precio de apertura de la vela.
**Coste:** mediana de la horquilla real de FTMO medida en el MT5 en la primera hora de cada apertura (índices sin comisión).

**Principal (variante 1):** cartera media diaria de los mercados disponibles, 2018-01 → 2026-11.
Variantes 2-3 (informativas, cuentan para el total): JP225 solo; costes ×2.
**Pasa si:** t neto de la cartera ≥ 2,4; segunda mitad > 0; costes ×2 > 0; supera al **placebo de lado**
(lado contrario, mismas salidas) y al **placebo de hora** (misma regla empezando 2 h después de la apertura).
Además: correlación diaria con el ORB US100 v018 < 0,3. Si falla, clase A o B en el registro, sin rescates.
