# Preregistro v4 ronda 7 (13-11-2026, antes de descargar)

Ronda 6 (candidato 8, ciclo de subastas del Tesoro en IEF 2002-2026): **NO PASA**. Supera t (2,62), 2ª mitad, costes ×2,
placebo y la réplica en ZN (t 3,5) y TLT (t 2,4), pero el DD a vol 15 % es 4,6 veces el beneficio anual (regla común < 3),
2016-2026 da ≈ +1 %/año con t < 0,5 y con solo las subastas de 10 y 30 años sale ≈ 0, al revés que el mecanismo.
Toda la ganancia está en ir largo los 4 días posteriores (el resto de días el bono rinde −0,2 %/año): dato curioso,
pero en la parte reciente ya no paga. Se registra como D (cae en la parte reciente).

## Candidato 9: apostar contra la beta (BAB) con ETF

- Pagador: inversores con límite de apalancamiento (fondos de pensiones, minoristas, fondos sin deuda) que para buscar
  más rentabilidad compran activos de beta alta y los sobrepagan (Frazzini y Pedersen 2014). Se cobra yendo largo de
  lo de beta baja apalancado y corto de lo de beta alta desapalancado.
- V1 (principal): los 9 ETF sectoriales Select Sector SPDR (XLB XLE XLF XLI XLK XLP XLU XLV XLY), 1999-2026, mercado SPY.
  Beta: 252 días de rendimientos diarios contra SPY, encogida 0,6·β + 0,4. Cada fin de mes (con datos hasta el día
  anterior, se opera al cierre del último día) largo de los 3 de beta más baja y corto de los 3 de beta más alta, peso
  igual dentro de cada pata, pata larga escalada a 1/β_L y corta a 1/β_H (beta neutra ex ante).
  Rendimiento = (1/β_L)(r_L − rf) − (1/β_H)(r_H − rf), rf = letra a 3 meses (^IRX).
- Costes: 0,02 % por lado sobre lo que se mueve en cada reajuste y 0,25 %/año de préstamo en la pata corta.
- Pasa si (reglas comunes): t neto diario ≥ 2,4; 2ª mitad > 0; costes ×2 > 0; supera el p95 del placebo (cada mes
  3 y 3 elegidos al azar con el mismo escalado, 200 repeticiones); DD a vol 15 % < 3 × beneficio anual.
- Réplica obligatoria (universo no mirado): mismo procedimiento con los ETF de país de iShares (EWA EWC EWD EWG EWH
  EWI EWJ EWK EWL EWM EWN EWO EWP EWQ EWS EWU EWW EWY EWT EWZ), mercado = media igual de los disponibles, 4 y 4;
  debe dar t ≥ 2.
- V3 (informativo): sectores sin escalado por beta (largo 3 bajas − corto 3 altas, mismo importe).
