# ORB de 5 min en acciones "en juego": DESCARTADO en P1 (13-11-2026)

Datos: M1 bid/ask de Dukascopy, 71 acciones grandes de EE. UU. (las 23 de la lista FTMO + 48 grandes),
2018-02 → 2026-11, bajadas y resumidas en GitHub Actions (`.github/workflows/descargar-acciones-m1.yml`,
`procesar.py`). Análisis: `analizar.py`. Fuera de muestra 2023-26 **sin abrir**.

## Ajuste 2018-2022 (R por operación; coste = media horquilla a la entrada y a la salida + 0,004 % por lado)

| Variante | Ops | Bruto | Coste | Neto | t neto | Placebo p95 (bruto) |
|---|---|---|---|---|---|---|
| En juego (VR ≥ 2, top 5), stop A 10 % ATR (paper) | 1.879 | −0,108 | 0,494 | −0,602 | −8,0 | −0,078 |
| En juego, stop B otro extremo del rango | 1.879 | +0,061 | 0,106 | −0,044 | −1,3 | +0,097 |
| Todas las acciones, stop A | 62.470 | −0,073 | 0,425 | −0,498 | −45 | −0,092 |
| Todas las acciones, stop B | 62.470 | +0,023 | 0,126 | −0,102 | −18 | +0,029 |

Neto por año (en juego, stop B): 2018 +0,10 · 2019 −0,13 · 2020 +0,09 · 2021 −0,11 · 2022 −0,18.

## Veredicto por puerta
- **P1 bruto ≥ 3× coste: NO.** El mejor caso (stop B) tiene bruto 0,6× el coste.
- **P1 placebo: NO.** Con dirección aleatoria en los mismos días y salidas el bruto medio es +0,049 R y el p95 +0,097: el +0,061 de la regla es la forma de la salida (stop corto + salida al cierre), no la dirección de la apertura.
- Stop A (el del artículo) pierde **incluso sin costes**: con un stop de 10 % del ATR, el ruido de minuto de una acción grande lo salta casi siempre (gana el 11 %), y la horquilla ya es media R.
- El volumen relativo alto mejora algo (+0,075 R bruto con VR 2-3 frente a 0,00 con VR < 0,8), pero sin llegar al coste.

Encaja con las réplicas públicas: el edge del artículo sale de valores pequeños y volátiles del universo de
7.000 acciones; en mega caps (lo que ofrece una prop de CFD) desaparece.

Herramientas: la descarga M1 de Dukascopy desde GitHub Actions funciona (614 acciones US disponibles con
ticks desde 2017): queda como vía para cualquier idea futura en acciones sin depender del PC.
