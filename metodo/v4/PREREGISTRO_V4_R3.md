# Preregistro v4 ronda 3 (13-11-2026, antes de descargar/calcular)

Ronda 2: candidato 3 (financiación transversal) NO PASA: t 2,38 < 2,4 (V2 solo precio t 1,47; casi todo en 2021).

## Candidato 4: decaimiento de los ETF apalancados por pares (corto del 3x alcista y del 3x bajista)

- Pagador: el que mantiene un ETF apalancado diario pierde por la composición (≈ (L²−L)/2·σ² al año) y paga
  comisiones de ~1 %. Vender en corto los dos lados del mismo índice deja la exposición casi neutra y cobra ese
  desgaste. Riesgo: tendencias fuertes sin vuelta (la composición favorece al ETF) y el coste de préstamo.
- Pares (todos los que existan en Yahoo): TQQQ/SQQQ, UPRO/SPXU, SPXL/SPXS, UDOW/SDOW, TNA/TZA, SOXL/SOXS, FAS/FAZ,
  TECL/TECS, LABU/LABD, ERX/ERY, NUGT/DUST, YINN/YANG.
- Regla: el primer día hábil de cada mes, corto del mismo importe en los dos ETF del par (50 % + 50 % del capital del
  par); se mantiene el mes sin reajustar. Cartera = media de los pares disponibles. Datos desde 2012.
- Coste: 0,05 % por lado y pata en cada reajuste + **préstamo 4 %/año por pata** (supuesto; el real no es público).
  Costes ×2 = préstamo 8 % y 0,10 % por lado.
- **V1 (principal):** todos los pares, mensual. V2 (informativo): solo índices amplios (TQQQ/SQQQ, UPRO/SPXU,
  SPXL/SPXS, UDOW/SDOW, TNA/TZA). V3 (informativo): reajuste semanal.
- Pasa si: t neto (diario) ≥ 2,4 en 2012-2026; segunda mitad > 0; costes ×2 > 0; positivo por separado en V2 y en el
  resto (sectoriales); DD a vol 15 % < 3 años de beneficio. Placebo: no hay lado aleatorio con sentido; el control es
  "corto solo del ETF alcista" y "corto solo del bajista" (si todo viene de un lado es una apuesta de dirección).

## Candidato 5: reversión semanal transversal en cripto (perpetuos)

- Pagador: el que necesita liquidez (liquidaciones, ventas forzadas) paga a quien la da; en cripto el apalancamiento
  y las liquidaciones son mayores que en acciones.
- Lunes 00:00 UTC, mismos 20 perpetuos: largo el tercio que más cayó en los 7 días previos, corto el que más subió,
  neutral, 7 días; rentabilidad con financiación; coste 0,07 % por lado y pata.
- **V1:** lo anterior. V2 (informativo): retorno de 1 día y reajuste diario. V3 (informativo): sin financiación.
- Pasa si: t neto ≥ 2,4; 2ª mitad > 0; costes ×2 > 0; supera el p95 de 300 ordenaciones aleatorias.
