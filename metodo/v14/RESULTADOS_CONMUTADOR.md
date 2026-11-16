# v14b · Conmutador por Hurst · resultados (16-11-2026)

Preregistro PREREGISTRO_CONMUTADOR.md (subido antes de ejecutar). Salida: salida_conmutador.txt.

## Veredicto: NO PASA (C1 y C2) → DESCARTADO, clase A (sin ventaja ni antes de costes en la pata nueva)

| Variante | Neto/op (t) | Pata sigue | Pata contra | Placebo p99 | Mercados + | Sharpe |
|---|---|---|---|---|---|---|
| C1 H 5 sesiones | −0,025 (−1,22) | +0,070 | **−0,116 (t −4,4)** | +0,018 | 1/4 | −0,30 |
| C2 H del día | −0,037 (−1,85) | +0,033 | **−0,108 (t −4,0)** | +0,019 | 1/4 | −0,45 |

- Ir en contra en régimen antipersistente pierde en los 4 mercados y con las dos medidas. Un Hurst bajo en M1 **no**
  anuncia que el movimiento de apertura se deshace: tras el rango de 10 min el precio sigue (o no hace nada), nunca
  revierte lo suficiente para pagar la horquilla.
- Informativo US100: la pata contra es ≈ 0 (+0,01 / −0,04): el conmutador es peor que el ORB solo (Sharpe 0,62-0,74
  frente a 1,00). Confirma que lo único que se ve en el US100 es "el ORB gana algo más con H alto", no un régimen
  explotable por sí mismo.

Sin rescates (ni solo la pata "sigue", que es el ORB filtrado ya descartado en v14, ni otros mercados).
La vía "sistema propio por Hurst" queda cerrada. Lo que sigue abierto es solo el seguimiento en real (v14c).
