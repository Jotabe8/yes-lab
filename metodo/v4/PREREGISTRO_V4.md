# Preregistro búsqueda v4: primas de riesgo (13-11-2026, escrito ANTES de descargar ni ver los datos)

Pedido de Jorge: encontrar ventaja en cualquier mercado sin tener en cuenta reglas de firmas, brókers, tamaño ni estilo.
Hipótesis de la v4: las 60 familias anteriores buscaban **ineficiencias de precio** (dirección, calendario, volatilidad
intradía) dentro de una cuenta prop, que prohíbe en la práctica mantener posiciones (swap, noticias, fin de semana).
Las ventajas más documentadas y persistentes no son ineficiencias sino **primas que alguien paga a cambio de quitarse
un riesgo**: el seguro contra caídas (prima de volatilidad) y el apalancamiento cripto (financiación de perpetuos).
Nunca se probaron porque no cabían en FTMO. Aquí se prueban en el instrumento real y con sus costes reales.

Reglas comunes: ≤ 3 variantes por candidato; serie diaria; t neto (día) ≥ 2,4 en el periodo completo; segunda mitad > 0;
costes ×2 > 0; supera el p95 del placebo de tiempo aleatorio (misma fracción de días expuesta, 1.000 permutaciones por
bloques de 20 días); señal con **un día de retraso** (la señal del cierre t se opera del cierre t+1 al t+2), para no usar
el cierre del índice VIX (16:15) contra la liquidación del futuro (16:00) ni la financiación ya conocida. Se publican
siempre la peor jornada, el peor mes, el DD máximo y el comportamiento en los choques conocidos (feb-2018, mar-2020,
ago-2024, mayo-2021, nov-2022 FTX). Una prima con colas puede tener t alto y arruinar: el listón añade **DD máximo
< 3 veces el beneficio anual medio** a tamaño de volatilidad 15 %/año.

## Candidato 1: prima de volatilidad en futuros VX (CBOE)

- Instrumento: futuros VIX (VX), liquidaciones diarias de CBOE 2013-2026. Posición corta en un futuro sintético de
  vencimiento constante a 30 días (mezcla del primero y segundo vencimiento por días hasta vencimiento, como el índice
  del VXX). Rentabilidad diaria = −Σ w_i ΔF_i / Σ w_i F_i (cartera reajustada cada día).
- Coste: 1 tick (0,05 pt) de horquilla + 2 $ de comisión por contrato y lado al entrar y salir, y el traspaso diario de
  ~1/21 de la posición entre vencimientos (2 patas × medio tick).
- **V1 (principal):** corto solo si VIX/VIX3M < 1 (curva en contango) con un día de retraso.
- V2 (informativo): corto siempre.
- V3 (informativo): V1 y además VIX < 30.
- Réplica en otro instrumento (obligatoria para pasar): misma regla V1 con el ETF SVXY/VXX (Yahoo, 2011-2026), corto VXX.
  Debe dar t ≥ 2 con su coste (0,02 % por lado).

## Candidato 2: carry de financiación en perpetuos cripto (Binance USDT-M)

- Instrumento: largo contado / corto perpetuo del mismo valor nominal (delta neutral) en 20 criptomonedas grandes,
  2020-2026. Rentabilidad diaria por moneda = r_contado − r_perpetuo + financiación cobrada ese día (cierres de las
  velas diarias UTC de los dos mercados, así entra el riesgo de base).
- Coste: 0,10 % contado + 0,05 % perpetuo por lado en cada entrada y salida (tarifa estándar sin descuentos).
- Señal: media de la financiación de los 7 días anteriores (un día de retraso). Cartera equiponderada entre las
  monedas con señal; día sin ninguna = 0. Moneda elegible tras 60 días cotizando ambos mercados.
- **V1 (principal):** abrir si la media 7 días > 0,01 % por 8 h (≈ 11 %/año), cerrar si < 0.
- V2 (informativo): siempre abierto en todas.
- V3 (informativo): solo BTC y ETH con la regla V1.
- Réplica obligatoria: V1 debe ser positiva con t ≥ 2 por separado en (a) BTC+ETH y (b) las 18 restantes.

## Qué NO cuenta como pasar
Un resultado que solo viene de un episodio (p. ej. 2021), o cuyo DD a vol 15 % supera 3 años de beneficio medio.
Cualquier cambio tras ver los datos se informa como exploratorio y no puede dar el veredicto.
