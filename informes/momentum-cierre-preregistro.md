# Momentum intradía al cierre en US100: reglas fijadas antes de mirar los datos

Fecha: 2026-10-25. Jorge pide probar el informe "Momentum intradía en índices" (Gao, Han, Li y
Zhou, 2018; Baltussen, Da, Lammers y Martens, 2021; Zarattini, Aziz y Barbon, 2024) como
complemento del ORB US100. Este archivo se sube antes de ejecutar ninguna prueba. Las reglas no
se reajustan después. Nada de esto es una recomendación de inversión.

## Antecedente

En el PC de Jorge (`nuevo_sistema/closing_mom.py`, 24/10/2026) ya se probó la regla básica:
signo del recorrido desde el cierre de ayer hasta las 22:30 servidor, operar 22:30-23:00.
Resultado: US100 2018-2026 +0,19 pb/día neto (t 0,2) y 2024-2026 −2,6 pb (t −2,5). Esa prueba
cobró un solo spread, no tenía deslizamiento, no separaba por volatilidad ni hacía
walk-forward, y no probó la primera media hora, la extensión del ORB ni la zona de ruido. Aquí se
completa lo que pide el informe. La prueba anterior cuenta como un intento más (no es una
muestra nueva).

## Datos

- Principal: US100.cash M1 de FTMO (`data/US100_cash_M1_FTMO.csv`), 2021-10-01 a 2026-09-30,
  precios bid con columna de spread (puntos = spread × 0,01). Son los mismos datos del ORB.
- Secundario (solo informativo): US100 M1 de Dukascopy 2018-01 a 2021-09.
- Horas del servidor (NY + 7). Solo se usan días con la apertura cash a las 16:30 servidor,
  comprobado por el salto de volumen. Si hay semanas de desfase horario (apertura a las 15:30)
  se excluyen enteras.

## Definiciones (hora del servidor)

- `C0`: cierre de la vela de las 22:59 del día hábil anterior.
- `P(hh:mm)`: apertura de la vela de esa hora. `P(23:00)` = cierre de la vela de las 22:59.
- `r_día = P(22:30)/C0 − 1`. `r_1ª = P(17:00)/C0 − 1` (Gao: cierre de ayer hasta 30 min tras la
  apertura). `r_apert = P(17:00)/P(16:30) − 1` (solo la primera media hora cash).
- `r_últ = P(23:00)/P(22:30) − 1`; variante `r_últ55 = P(22:55)/P(22:30) − 1`.
- Volatilidad del día (conocida a las 22:30): desviación de los retornos M1 de 16:30 a 22:30.
  Terciles con los cortes del periodo de ajuste (o de toda la muestra en la regresión descriptiva).

## Prueba 1. Regresión

MCO de `r_últ` sobre `r_día`, sobre `r_1ª` y sobre `r_apert`, con t de Newey-West (5 retardos).
Por año natural y por tercil de volatilidad. Se informa también la tasa de acierto del signo.

## Prueba 2. Estrategia complementaria

- A las 22:30 se entra en el signo de `r_día` (sin filtro). Salida a las 22:55 (principal) o a
  las 22:59 (variante). Stop de protección a 1 R = 15 % del ATR14 diario del día anterior (la misma
  unidad que el ORB), comprobado con máximos y mínimos M1.
- Costes: largo compra a ask (bid + spread de la vela) y vende a bid; corto al revés. Más 0,2
  puntos de deslizamiento por lado. Costes al doble: spread × 2 y 0,4 puntos por lado.
- Antes de nada se mide el spread real de 22:30 a 23:00 (mediana y percentil 90 por minuto).
- Walk-forward 3 + 1: ajuste 2021-10 → 2024-09, prueba 2024-10 → 2025-09; ajuste 2022-10 →
  2025-09, prueba 2025-10 → 2026-09. En el ajuste se elige entre 6 variantes como mucho: señal
  `r_día` o `r_1ª` × filtro de volatilidad {ninguno, tercil alto, mitad alta}. Criterio de
  elección: R medio neto con costes normales. La variante sin ajuste (`r_día`, sin filtro) se
  informa siempre.

**Criterio de aceptación** (el del informe): R medio neto > 0 con costes al doble en las dos
ventanas fuera de muestra, y que al combinarla con el ORB la caída máxima combinada (en R, misma
fracción de riesgo) suba menos de lo que suma en beneficio en el mismo periodo. Además, el t
conjunto de las dos ventanas fuera de muestra con costes normales tiene que ser > 1 para no tomar
ruido por señal.

## Prueba 3. Extensión del ORB

Se reconstruye el ORB tal cual (`walkforward/sim.py`: rango de 10 min, cuerpo ≥ 10 %, R = 15 %
ATR, trailing a 3 R con distancia 1 R) con las velas hasta las 22:55. Para las operaciones aún
abiertas a las 22:30:

- Base: cerrar a las 22:30 (como el EA).
- Extensión: si la dirección del ORB coincide con el signo de `r_día`, mantener hasta las 22:55
  con el mismo stop/trailing; si no, cerrar a las 22:30.
- Control: mantener todas hasta las 22:55 (separa el efecto de la señal del de alargar).

Se compara el R por operación del ORB entero, con el spread del cierre a las 22:55 y costes al
doble, en todo el periodo y en los dos años fuera de muestra. Pasa si mejora el R medio con
costes al doble en los dos años fuera de muestra y la diferencia frente al control es positiva.

## Prueba 4 (opcional). Zona de ruido de Zarattini, Aziz y Barbon

Parámetros del artículo sin tocar: `σ(t)` = media de |P(t)/P(16:30) − 1| a esa misma hora en los
14 días anteriores. Banda superior = máx(P(16:30), C0) × (1 + σ), inferior = mín(P(16:30), C0) ×
(1 − σ). Comprobación cada media hora (17:00, 17:30 … 22:30). Si el cierre M1 previo está por
encima de la banda superior, largo; por debajo de la inferior, corto. Stop dinámico en el borde
de la zona o el VWAP de la sesión (el más cercano al precio que proteja), revisado cada media
hora; salida a las 22:55. Una sola posición, puede darse la vuelta. Tamaño fijo en R (1 R = 15 %
ATR, para comparar con el ORB), no el apalancamiento por volatilidad del artículo. Mismos costes.
Sin ajuste: se informan las dos ventanas fuera de muestra y el periodo completo. Mismo criterio
que la prueba 2. Ojo: se solapa con el ORB en horario y dirección; se mide la correlación diaria.

## Prueba 5. EV por cuota

Solo informativo si nada pasa: se añade el R diario de la variante sin ajuste al del ORB
(`walkforward/orb_R_2018_2026.csv`) y se pasa por el simulador de `cartera/anio_100k.py`
(2-Step 100K, reto 2 %, fondeada 1,5 %, mismo coste extra de 0,05 R por operación) para ver la
diferencia en neto medio por año frente al ORB solo.
