# Preregistro: rebalanceo por umbral de fondos 60/40 (señal diaria) — 2026-11-14, antes de mirar resultados

Fuente: Harvey, Mazzoleni y Melone, "The Unintended Consequences of Rebalancing" (NBER w33554, 2025; versión EDHEC 2026, SSRN 5122748).
Réplica independiente con futuros: Quant Returns, "Can you front-run institutional rebalancing?" (Sharpe > 1,4).
Lo que el proyecto ya probó (2026-10-26) fue SOLO la pata de calendario (fin de mes, 5 sesiones): bruto 1,3× coste, bajo placebo.
La pata de **umbral** (diaria, ~16 rebalanceos/año por banda) no se ha probado nunca.

Pagador: fondos de pensiones y balanceados que rebalancean cuando el peso de acciones se aleja del 60 %.

## Señal (fija)
- Cartera 60/40 simulada con ^GSPC (cierre) y futuro ZN=F (cierre), desde 2000-09-21.
- Para cada banda δ = 0,0 %, 0,1 %, …, 2,5 % (26 bandas): el peso deriva con los retornos; al cierre del día t, d = w − 0,60.
  Si |d| > δ → señal_δ = d y w vuelve a 0,60; si no, señal_δ = 0. S_t = media de las 26 señales.
- z_t = S_t / desviación de S en 2000-09 → 2023-03-17 (periodo del paper). S > 0 = acciones sobreponderadas = venta prevista.

## Pruebas (3 variantes como máximo)
1. Principal: z ≥ +1 → corto US500 de cierre t a cierre t+1; z ≤ −1 → largo. Coste: 0,6 pb por entrada y por salida + 3 pb por noche (swap, ambos lados).
2. Intradía sin swap: mismo signo, de apertura t+1 a cierre t+1 (SPY, 2010+), coste 0,6 pb ida y vuelta.
3. Umbral |z| ≥ 0,5 en la versión 1.

## Listón (v3)
- Historia completa 2000-2026: neto t ≥ 2,4; segunda mitad > 0; costes ×2 > 0.
- Tramo no visto por el paper (2023-03-20 → 2026-11-13): neto > 0.
- Placebo: 500 desplazamientos circulares de la señal (≥ 20 días): resultado > p95.
- Control: la regresión de r(t+1) sobre z sigue negativa con r_acciones(t) y r_acciones−r_bonos(t) como controles (si no, es la reversión de 1 día ya descartada en "noche tras estrés").
- Sin 2008 y 2020 > 0 (asimetría 5,2 del paper = riesgo de que todo sean dos crisis).
- ≥ 40 ops/año; corr diaria con ORB v018 < 0,3.
