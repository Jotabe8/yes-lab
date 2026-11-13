# Filtro de hueco para el ORB US100: DESCARTADO (13-11-2026)

Regla fijada con 2012-2022: operar el ORB solo si el hueco de apertura > +0,262 % (percentil 66 de 2012-22).
Mirada una vez en 2023-2026. Réplica Python, neto con 1 punto de coste; y serie real v018.

| Periodo | Hueco bajo | Medio | Alto (filtro) | Todos |
|---|---|---|---|---|
| 2012-17 réplica (R neta/op) | −0,19 | −0,12 | **+0,24** | −0,04 |
| 2018-22 réplica | **+0,37** | +0,03 | +0,22 | +0,23 |
| 2023-26 réplica | +0,16 | −0,01 | +0,23 | +0,14 |
| 2023-26 serie real v018 | — | resto +0,24 (526 ops) | +0,13 (268 ops) | — |

- En 2023-26 la réplica mejora la R por operación con el filtro (+0,23 frente a +0,14), pero opera un tercio
  de los días y la R total baja (74 R frente a 127 R).
- En la serie real del EA (v018, con sus filtros y gestión) pasa lo contrario: los días de hueco alto rinden
  menos (+0,13 R) que el resto (+0,24 R).
- En 2018-22 los mejores días eran los de hueco bajista. El patrón no es estable.
**Veredicto: no se añade al EA.** Script en `orb_acciones/` (datos `orb_us100_con_hueco.csv`).
