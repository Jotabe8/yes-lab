# ORB US100 en 2012-2017: fuera de muestra nuevo con datos gratis de Dukascopy (13-11-2026)

Réplica en Python de la lógica v017/v018, sin trailing ni filtros: rango 9:30-9:40 NY, dirección de la vela del
rango (cuerpo ≥ 10 %), entrada 9:40, stop 15 % del ATR14 y salida 15:55, con el stop comprobado en M1 con bid/ask.
Calibración con la serie real v018 en 1.769 días comunes: correlación de R 0,74.

| Periodo | Ops | R bruta | t | R neta (1 punto ida y vuelta) | t |
|---|---|---|---|---|---|
| 2012-2017 (nuevo) | 1.318 | **+0,130** | 2,0 | −0,037 | −0,6 |
| 2018-2022 | 1.156 | +0,280 | 3,5 | +0,226 | 2,8 |
| 2023-2026 | 910 | +0,168 | 1,9 | +0,140 | 1,6 |

Bruto por año 2012-17: +0,22 · +0,05 · +0,25 · +0,07 · +0,24 · −0,04 (5 de 6 positivos).

- **El mecanismo del ORB ya funcionaba antes de 2018.** Es la primera confirmación fuera de toda la muestra
  usada para diseñarlo.
- Entonces no daba dinero neto por el coste, no por falta de edge. El índice estaba en 2.500-6.500 puntos y
  el stop (15 % del ATR) era de 4-8 puntos, así que 1 punto de horquilla costaba 0,12-0,38 R. Hoy el ATR es
  de 200-380 puntos y el mismo punto cuesta 0,02-0,05 R.
- Riesgo para el EA en real: el edge bruto de 2012-17 (+0,13 R) es la mitad del de 2018-22. Una vuelta a una
  volatilidad muy baja reduciría el beneficio, aunque con el índice en 25.000 puntos el coste seguiría siendo pequeño.
- Aviso de datos: en 2012 Dukascopy no tiene horquilla (bid = ask); el bruto de 2012 es fiable, el neto no.
