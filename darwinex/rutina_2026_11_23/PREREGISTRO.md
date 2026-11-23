# Preregistro de la rutina semanal (23-11-2026): dos pruebas

Escrito y subido ANTES de ejecutar nada sobre `datos_bonos/`. Ninguna de las dos reglas se ha calculado todavía
con estos datos. Aviso honesto: el 16-11 se sondeó la pata corta de principio de mes SIN condición (10 años de FRED,
3 primeras sesiones: −0,1 pb en 1990-2026), y otro hilo descartó el rebalanceo de pensiones de fin de mes
(registro de ideas, clase D). La prueba A añade una condición que no se ha mirado.

## A. Pata corta condicionada a principio de mes (bonos, Darwinex Zero)

**Fuente:** Beyond Passive Investing, "Two Calendar Effects at the Month Boundary" (5-4-2026). TLT y VTI,
2002-08 → 2025-06, 273 meses. Corto de TLT las 5 primeras sesiones del mes si la bolsa batió a los bonos en las
15 primeras sesiones del mes anterior: percentil 100 frente a 10.000 permutaciones. Sin costes.

**Mecanismo propuesto:** rebalanceo de carteras mixtas que se ejecuta al principio del mes siguiente. Si la bolsa
subió más que los bonos, el rebalanceo compra bolsa y vende bonos en los primeros días.

**Regla fija:**
- Señal: retorno del S&P 500 (`GSPC.csv`, precio) menos retorno del 10 años (FRED, retorno ≈ −8,5·Δy + y/252) en
  las 15 primeras sesiones del mes M. Si es > 0, corto del 10 años del cierre de la última sesión de M al cierre
  de la 5.ª sesión de M+1. Si no, fuera.
- Coste 3 pb por operación (como el preregistro del 16-11); ×2 = 6 pb.

**Periodos:**
- Fuera de la muestra publicada (lo que decide): 1990-01 → 2002-07 y 2025-07 → 2026-10, juntos.
- Informativo: periodo completo 1990-2026 y tramo publicado 2002-08 → 2025-06 (réplica de su resultado).

**Pasa si:** en el tramo fuera de muestra el neto por operación es > 0 con t neto ≥ 2,0 (potencia baja: ~80
operaciones), en el periodo completo t neto ≥ 2,4, costes ×2 > 0 en el periodo completo, y el placebo (la misma
señal pero corto de las sesiones 6 a 10 de M+1) da menos que la regla.

**T0:** el artículo da +0,68 pp por operación en TLT (duración ~17). En el 10 años equivale a ~+34 pb. Con
volatilidad de 5 sesiones de ~90 pb y ~80 operaciones fuera de muestra, t ≈ 3,4 si el efecto se mantiene entero.

## B. Tendencia a corto plazo en futuros de tick grande (Treasuries, Darwinex Zero)

**Fuente:** Kurth, Eisler, Rej y Bouchaud, "Is Trend Still Your Friend?" (arXiv 2607.01550, 3-7-2026). En ~100
futuros, la tendencia corta perdió casi todo el Sharpe tras 2009 (τ = 20: 0,79 → 0,27), salvo en los contratos de
tick grande, que siguen en 1,0-1,2. Explicación microestructural: en tick grande la cola de órdenes revela la
presión y el precio se ajusta más despacio.

**Instrumentos:** ZT, ZF, ZN y ZB continuos (`datos_bonos/`), todos de tick grande. Control: ES (tick pequeño en
relación a su volatilidad), donde el artículo predice poco.

**Regla fija:**
- Retorno diario del futuro; los saltos de vencimiento se detectan contra FRED (retorno del futuro menos β·retorno
  de FRED > 4 desviaciones) y se sustituyen por β·retorno de FRED de ese día.
- Señal = (EWMA_20 − EWMA_80) del precio acumulado, dividida por la desviación de los retornos de 60 días;
  posición = señal normalizada por su desviación de 250 días, recortada a ±2, a volatilidad objetivo igual por
  contrato. Retardo de un día (la posición de hoy usa la señal de ayer).
- Cartera: media de los 4 contratos.
- Coste: 1 tick por lado sobre el cambio de posición (ZT 0,4 pb, ZF 0,7 pb, ZN 1,5 pb, ZB 2,7 pb del nominal);
  ×2 como sensibilidad.

**Periodos:** principal 2009-07 → 2026-10 (posterior a la ruptura del artículo). Informativo: 2001-2009-06.

**Pasa si:** t neto de la cartera ≥ 2,4 en el periodo principal; segunda mitad > 0; 2019-2026 > 0; costes ×2 > 0;
y la cartera de Treasuries bate al control ES en Sharpe neto. τ = 5, 10 y 50 solo se informan.

**T0:** para t 2,4 en 17,3 años hace falta Sharpe neto 0,58. El artículo da 1,0-1,2 con decenas de contratos de
tick grande; con 4 contratos muy correlacionados es probable que se quede corto. Un "no pasa" con Sharpe > 0
será clase C.
