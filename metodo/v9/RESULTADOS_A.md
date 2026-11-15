# Resultado v9-A: ruptura en el instante del dato programado — DESCARTADA

Preregistro: `PREREGISTRO_EVENTOS.md` (commit anterior a los datos). Código `eventos.py`, `analizar_a.py`,
salida completa en `salida_a.txt`, operaciones en `ops_a_v1.csv`. Motor comprobado con paseo aleatorio sintético
(8 semillas: +0,019 ± 0,014 R, sin sesgo).

| | Ops | Días | Bruto R (t) | Coste R | Neto R (t) |
|---|---|---|---|---|---|
| **V1 principal** (vela 5 min, stop 0,15 ATR, 3 h) | 2.801 | 478 | **+0,000 (0,00)** | 0,122 | −0,121 (−1,82) |
| V2 (salida 1 h) | 2.801 | 478 | −0,046 | 0,121 | −0,166 |
| V3 (stop 0,30 ATR) | 2.801 | 478 | −0,013 | 0,060 | −0,073 |
| Placebo lado contrario | 2.801 | 478 | +0,039 (0,61) | 0,121 | −0,082 |
| Placebo misma hora, días sin dato | 38.933 | 3.629 | −0,008 | 0,121 | −0,132 |

- Evento − placebo: +0,010 R (t 0,15). Por evento: NFP bruto −0,14 (t −1,6), IPC +0,05, FOMC +0,18 (t 0,9).
  Por mercado ninguno supera t 1,1 en bruto; US100 y US500 negativos en bruto.
- La horquilla real en el minuto del dato (Dukascopy) se come 0,12 R por operación; aunque FTMO fuera algo más
  barata, **no hay ventaja bruta que proteger**: la primera vela tras el dato no dice hacia dónde sigue el precio.
- Falla las puertas 1, 2, 3 y 5. Clase A (sin bruto). Familia cerrada: no repetir con otros datos programados
  (ISM, ventas minoristas, BCE…), porque los tres de mayor impacto no muestran nada.
