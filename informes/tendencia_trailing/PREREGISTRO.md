# Preregistro: tendencia con operaciones largas y trailing stop (2026-10-30)

Escrito antes de mirar resultados.

- **Regla principal (fija):** ruptura Donchian de 55 días al cierre (cierre > máximo de los 55 días
  anteriores → largo; cierre < mínimo → corto), entrada a la apertura siguiente. Stop inicial 3 ATR(20).
  Trailing tipo chandelier: stop = máx(stop, máximo desde la entrada − 3 ATR) (simétrico en cortos),
  comprobado vela a vela, huecos al precio de apertura. Sin objetivo. Una posición por mercado.
  1 R = distancia del stop inicial.
- **Variantes declaradas (n_pruebas = 18):** canal 20/55/100 × trailing 2/3/4 ATR × {ambos lados, solo largos}.
  Se informa de todas; la principal es 55/3/ambos.
- **Mercados:** los diarios de Yahoo de lo que se puede operar en CFD de prop (13 índices, 11 pares,
  metales, energía, agrícolas, cripto). Se evalúa la cesta y cada grupo; no se eligen mercados a posteriori.
- **Periodos:** ajuste 2005-2022 (la tendencia da pocas operaciones por mercado y necesita años),
  prueba 2023-2026 abierta una sola vez.
- **Costes:** spread en % del precio por mercado y **financiación nocturna con tipos reales** (FRED):
  largo índice/materia paga r + m, corto cobra r − m; forex paga/cobra el diferencial ± m.
  Recargo m: escenario normal (índices 2,5 %, forex 1 %, metales 2,5 %, energía/agrícolas 3 %,
  cripto 15 %) y escenario FTMO (índices 6,5 %, observado en el Strategy Tester del IndexBasket).
- **Métrica y umbral:** R neta media por operación de la cesta. Pasa P1 si bruto ≥ 3× coste,
  supera el p95 de un placebo con las mismas salidas (entrada en día y dirección aleatorios,
  mismo nº de entradas por mercado, 200 réplicas) y es positivo en ≥ 3 grupos de mercados.
  P3: prueba 2023-26 > 0 con t ≥ 1. P4: EV/cuota 2-Step > control y correlación diaria con el ORB US100 < 0,3.
