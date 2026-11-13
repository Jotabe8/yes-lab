# Preregistro: prima nocturna en futuros de índices US para Darwinex Zero (13-11-2026)

Escrito y subido antes de calcular nada. Proceso v3 (`metodo/BUSQUEDA_V3.md`).

## Origen
- Concretum (Pagani, "Breaking the Rules of Intraday Trading", 2026): la tendencia intradía en SPY gana si
  guarda de noche **solo los largos** (CAGR 14 → 20 %). Mecanismo conocido: prima nocturna (Cliff, Cooper y
  Gulen 2008; Kelly y Clark 2011; Lou, Polk y Skouras 2019): casi toda la rentabilidad del índice llega de
  noche.
- En el proyecto ya se probó en CFD de FTMO (clase B: bruto 0,02-0,07 % ≈ spread + swap). Regla v3: una B se
  reabre en un lugar más barato. Darwinex Zero tiene cuenta de futuros CME sin swap y sin pérdida máxima.
- T0: con el Sharpe publicado (~0,9) dividido por 2, la potencia es corta. Se prueba igualmente porque los
  datos ya están (coste cero) y es la vía "B en un lugar más barato".

## Datos
M1 Dukascopy precio medio bid/ask (yes-lab rama 1ei3pv, `orb_acciones/indices_2012/` + `indices/`):
US500, US100 (desde 2011-09) y US30 (desde 2013) hasta 2026-11-12. Precio de 15:55 (`p1555`) y apertura
9:30 (`o930`) de cada sesión, hora NY.

## Regla (una sola especificación)
- Compra a las 15:55 de cada sesión y vende a la apertura 9:30 de la siguiente (fines de semana y festivos
  incluidos: se mantiene hasta la siguiente sesión).
- Rentabilidad tipo futuro: precio de contado + (dividendo − tipo a 3 m) × días naturales / 365. Dividendo
  fijo US500 1,8 %, US100 0,8 %, US30 2,0 %; tipo = media anual del T-bill a 3 meses (tabla fija en el
  script).
- Coste por ida y vuelta (1 tick + 5 $ de comisión por contrato): ES 0,6 pb, NQ 0,3 pb, YM 0,5 pb.
- Cartera principal: media equiponderada de los mercados disponibles cada día.

## Criterios (todos)
1. t neto (Sharpe diario × √n) ≥ 2,4 en toda la historia.
2. Segunda mitad neta > 0.
3. Con costes × 2, neto > 0.
4. Supera a los dos placebos en Sharpe: (a) siempre comprado tipo futuro en los mismos mercados;
   (b) la pierna intradía 9:30 → 15:55.
5. Valor en Darwinex Zero: mezclada a igual riesgo con el ORB US100 v018 (serie mensual 2018-26, R con BE
   − 0,05), sube el Sharpe mensual ≥ 0,10 **y** más que el siempre comprado.

Si falla cualquiera: descartada (regla de Jorge: no se deja en reserva). Se informa por mercado y por año
solo como información.
