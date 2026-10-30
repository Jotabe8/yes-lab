# Preregistro: ruptura intradía tras día estrecho (NR7, Crabel) (2026-10-30)

Escrito antes de mirar resultados. Hipótesis (Crabel, 1990): tras una compresión de rango el día
siguiente tiende a expandirse en una dirección; quien vende volatilidad barata la recompra.

- **Regla:** si el rango de ayer es el más estrecho de los últimos 7 días (NR7), hoy se coloca una
  orden stop de compra en el máximo de ayer y otra de venta en el mínimo (OCO). Si la apertura ya
  está fuera, se entra a la apertura. Stop en el otro extremo de ayer. Salida al cierre del día
  (intradía, sin swap). R = (salida − entrada) / (entrada − stop).
- **Ambigüedad diaria:** si el día toca los dos extremos se cuenta −1 R (peor caso), igual en el placebo.
- **Variantes:** NR7, NR4 y día interior (inside day). n_pruebas = 3. Principal: NR7.
- **Mercados:** 13 índices + XAUUSD, XAGUSD, WTI, BRENT, COPPER (diarios de `datos_tendencia/`).
- **Periodos:** ajuste 2000-2022, prueba 2023-2026 abierta una vez.
- **Costes:** spread ida y vuelta (índices EE. UU. 0,02 %, resto 0,04 %, metales/energía 0,03-0,1 %)
  más 0,02 % de deslizamiento por la orden stop.
- **Umbral P1:** bruto ≥ 3× coste, por encima del p95 del placebo (misma mecánica en días no
  estrechos al azar, mismo nº por mercado, 500 réplicas) y positivo en ≥ 2/3 de los mercados.
