# Preregistro v4 ronda 2 (13-11-2026, escrito antes de calcular)

Contexto: ronda 1 → prima de volatilidad en VX descartada (t 0,79); carry de financiación cripto pasa el preregistro
pero su exceso sobre letras es ≈ 0 desde 2025. Jorge pide seguir con ideas nuevas.

## Candidato 3: la financiación como señal de posicionamiento (corte transversal en perpetuos)

- Mecanismo / pagador: una financiación alta indica largos apalancados apiñados que pagan por mantenerse; cuando se
  deshacen (liquidaciones, cansancio) la moneda rinde menos que las demás. Información nueva (posicionamiento), no el
  propio precio.
- Universo: los 20 perpetuos USDT-M de Binance ya descargados, elegible tras 60 días. Lunes 00:00 UTC: ordenar por la
  financiación media de los 7 días previos (ya conocida). **Corto el tercio con financiación más alta y largo el tercio
  más bajo**, pesos iguales, neutral en dólares, solo perpetuos, 7 días. Rentabilidad = precio + financiación
  cobrada/pagada. Coste 0,05 % comisión + 0,02 % deslizamiento por lado y pata sobre la rotación.
- **V1 (principal):** lo anterior. V2 (informativo): solo la parte de precio (sin financiación). V3 (informativo):
  quintiles extremos.
- Pasa si: t neto (diario) ≥ 2,4 en 2020-03 → 2026-11; segunda mitad > 0; costes ×2 > 0; supera el p95 de 1.000
  ordenaciones aleatorias; y **V2 > 0** (si solo gana por la financiación es el carry de la ronda 1 con otro nombre).

## Descartado en T0 sin datos
- Deriva del precio alrededor de la hora de cobro de la financiación (00/08/16 UTC): efecto esperado de pocos pb por
  evento frente a 7-14 pb de coste ida y vuelta en perpetuos. Margen < 2.
