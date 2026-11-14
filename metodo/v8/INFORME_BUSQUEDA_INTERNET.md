# Búsqueda en internet de estrategias no probadas (2026-11-14)

Punto de partida: ~85 familias ya registradas en `metodo/v3/registro_ideas.csv` y las notas de descartes (oct, nov, v7).
Fuentes revisadas: SSRN y arXiv 2025-26, NBER, Concretum (catálogo 2024-26), Quantpedia (blog hasta oct-2026), MQL5 blogs, Substack cuantitativos.

## Lista corta priorizada (solo lo que no estaba probado)

| # | Idea y fuente | Encaje | Veredicto |
|---|---|---|---|
| 1 | **Rebalanceo por umbral de fondos 60/40** (Harvey, Mazzoleni, Melone, NBER w33554 2025 / SSRN 5122748; réplica Quant Returns). Pagador identificable; el proyecto solo había probado la pata de fin de mes | US500 D1, ~25 ops/año, corr ORB 0,00 | **Probada (P1 preregistrado): NO PASA.** Replica el paper (t 3,3 neto 2000-26), pero en el tramo que el paper no vio (mar-2023 → nov-2026) −9,7 pb/op; versión intradía sin swap t 1,8; 25 ops/año < 40 |
| 2 | Zona de ruido / noise-band (Chuk SSRN 7609644 2026 en NQ; Paz SSRN 7290621 fuera de muestra en SPY; Concretum "Fast Alphas" feb-2026) | Nueva solo en GER40/UK100 (en US100 ya clase D y correlada con el ORB) | **Probada (P1 preregistrado, pedido por Jorge): NO PASA.** Cartera neto +0,002 R t 0,16; GER40 solo t 1,61 (costes ×2 t 0,86); UK100 y réplica EU50 sin bruto |
| 3 | Deriva previa a BoE, BoJ, SNB (Quantpedia 2025) | ~24 eventos/año, D-2 a D-1 con noches | Fuera en T0: < 40 ops, swap FTMO, el pre-FOMC análogo desapareció (Kurov et al.), sin magnitudes publicadas |
| 4 | Momentum intradía FX con amplificación del yen (Seeck, SSRN 7008318, 2026) | FX intradía | Fuera en T0: el propio paper concluye "barrera de coste para minoristas"; FX intradía ya es clase B en el proyecto |
| 5 | Momentum intramensual de sectores (Quantpedia ago-2026) | ETF sectoriales | Fuera: no hay CFD de sectores en FTMO/Darwinex; Sharpe 0,55 |
| 6 | Momentum intradía global (Li, Sakkas, Urquhart 2022) | Índices de contado | Fuera: precios de contado rancios (mismo artefacto que NR7); en US100 sin efecto |
| 7 | Flujo minorista matinal SPY y aceleración de correlaciones ETF (Quantpedia 2026) | — | Fuera: dato de pago / es una cobertura, no un sistema |

Confirmación externa de la lección del proyecto: Mesfin (arXiv 2605.04004, 2026) prueba 14 familias intradía OHLCV en MNQ y ninguna pasa; Strategy Lab (Substack) y un blog MQL5 replican el ORB en 5 índices con "bruto reproducido, neto cero" fuera del US100.

## Prueba de la candidata 1 (archivos en esta carpeta)

`PREREGISTRO_REBALANCEO_UMBRAL.md` (escrito antes de ejecutar), `rebalanceo_umbral.py`, `rebalanceo_umbral_salida.txt`.
Datos: ^GSPC y ZN=F diarios 2000-09 → 2026-11 (ya en yes-lab `metodo/v4/datos`).

| Listón | Resultado | ¿Cumple? |
|---|---|---|
| Neto toda la historia t ≥ 2,4 | +25,9 pb/op, t 3,33 | Sí |
| 2.ª mitad > 0 / costes ×2 > 0 | +23,5 pb (t 1,8) / +22,4 pb (t 2,9) | Sí |
| Placebo (500 desplazamientos) | 17.057 pb vs p95 1.766 | Sí |
| Sin 2008 ni 1S-2020 | +17,6 pb t 2,9 | Sí |
| Corr con ORB v018 / DD a vol 15 % | 0,004 / 20,5 % (< 3 × 9,7 %) | Sí |
| **Tramo no visto por el paper (2023-03 → 2026-11)** | **−9,7 pb/op (52 ops); regresión t −0,3** | **No** |
| **≥ 40 ops/año** | **25** (con umbral 0,5: 52 ops pero no visto +1 pb) | **No** |
| Versión intradía sin swap (para FTMO) | +11 pb t 1,8; no visto +2 pb | No |

Lectura: el efecto existió de 2000 a 2023 y el paper lo mide bien, pero desde su publicación no aparece, y para FTMO necesita dormir posiciones (swap) porque de apertura a cierre se queda en la mitad. Por la regla de Jorge, descartada sin reserva.

## Conclusión

Internet no trae una familia nueva que pase. Las dos candidatas probadas (rebalanceo por umbral y zona de ruido en Europa) fallan el listón. El ORB US100 sigue siendo el único sistema.

## Prueba de la candidata 2: zona de ruido en GER40 y UK100

`PREREGISTRO_ZONA_RUIDO.md`, `zona_ruido.py` (workflow `v8-zona-ruido.yml`, Dukascopy M1 bid/ask 2013-26), `zona_ruido_analisis.py`, `zona_ruido_salida.txt`.

| Mercado | Bruto | Neto (coste FTMO) | Costes ×2 | Contraria (placebo) |
|---|---|---|---|---|
| GER40 | +0,026 R t 2,36 | +0,018 R t 1,61 | t 0,86 | t −2,85 |
| UK100 | +0,005 R t 0,40 | −0,012 R t −1,07 | t −2,52 | — |
| EU50 (réplica) | −0,002 R t −0,14 | −0,041 R | — | — |
| **Cartera GER40+UK100** | +0,014 R t 1,49 | **+0,002 R t 0,16** | t −1,17 | t −2,48 |

Corr con ORB 0,03 y supera el placebo de signo en bruto, pero el neto de la cartera es cero (listón t ≥ 2,4) y la réplica no tiene bruto. En GER40 aparece la misma ventaja pequeña que ya vimos en el ORB GER40 (t 1,58): real pero demasiado fina. Clase C, descartada.
