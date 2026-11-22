# v19 · Tendencia diaria (momentum de series temporales) en una cesta cripto — preregistro

Escrito el 22-11-2026 antes de correr ningún backtest de esta familia. Solo se han mirado formatos y fechas de los ficheros.

## Origen y antecedentes
- Literatura: momentum de series temporales de 1-4 semanas en cripto (Liu y Tsyvinski 2021, *Risks and Returns of
  Cryptocurrency*, RFS; Liu, Tsyvinski y Wu 2022, JF). Publicado ≤ 2022: 2023-2026 (casi 4 años) es fuera de muestra
  real tras la publicación, así que la regla de origen se cumple.
- Mecanismo de flujo: inversores minoristas que persiguen precio y atención (entradas tardías tras subidas), sin
  vendedores de volatilidad que lo arbitren; variable de estado = rendimiento de 4 semanas de cada moneda.
- Ya cerrado en el proyecto y distinto de esto: momentum TRANSVERSAL semanal en 131 perpetuos (v4 candidato 6, t 0,29),
  reversión semanal cripto (v4, t −1,8), ORB cripto (v6), intradía CFD cripto (v3). Aquí cada moneda se compara solo
  consigo misma (comprado o fuera), que es otra apuesta: cronometrar la beta.

## Regla (única especificación principal)
1. Universo: 20 monedas grandes de Binance contado (`metodo/v4/datos/bn_*_spot1d.csv.gz`: ADA ATOM AVAX BCH BNB BTC DOGE
   DOT EOS ETC ETH FIL LINK LTC NEAR SOL TRX UNI XLM XRP), velas diarias 00:00 UTC, 2019-01 → 2026-10.
2. Cada lunes 00:00 UTC (con el cierre del domingo): señal = signo del rendimiento de 28 días. Si > 0, comprado
   7 días; si no, fuera. Una moneda entra cuando tiene 60 días de historia.
3. Tamaño: nocional 1/σ, con σ = desviación de los rendimientos diarios log de los 30 días previos × √7. 1 R = 1 σ
   semanal de la moneda. Cada moneda-semana comprada es una "operación".
4. Costes por lado sobre el nocional movido (|ΔN|, la salida se carga a la última semana comprada) y swap por noche:
   - **Exchange** (referencia): 0,10 % por lado (comisión 0,075-0,10 % + horquilla), sin swap.
   - **Darwinex Zero CFD**: 0,05 % comisión + horquilla 0,03 % (BTC ~11 $ ≈ 0,016 %; resto supuesto) = 0,08 % por lado;
     swap largo supuesto 20 %/año del nominal (no publicado: se da además el swap de equilibrio).
   - **FTMO** (Swing): 0,05 % por lado (horquilla + comisión) y swap largo supuesto 25 %/año (sin verificar; se da el de equilibrio).
5. Periodo de ajuste 2019-2022; fuera de muestra 2023-01-01 → 2026-10 (se abre una vez).

## Placebo, nulos y réplica
- Placebo (200): misma cesta y tamaños, pero cada moneda-semana comprada con probabilidad igual a la fracción real de
  semanas compradas de esa moneda, al azar. Mide si el *momento* de estar dentro aporta algo sobre la beta.
- Paseo aleatorio (20): velas diarias barajadas por moneda (`velas_paseo`, sin estacionalidad), mismo motor → R ≈ 0.
- `sin_fuga` sobre la señal.
- Réplica: las ~106 monedas de `metodo/v4/datos/*_spot1d.csv.gz` sin prefijo `bn_` (otro universo), misma regla.

## Métrica y umbrales (los de metodo/embudo.py, t por semana)
- P1: bruto ≥ 3× coste, bruto > p95 del placebo, funciona en la réplica (t > 1 y mismo signo).
- P2: neto > 0 con coste ×2, ≥ 60 % de años positivos, meseta en lookback 22/34 días (±20 %).
- P3: OOS 2023-26 > 0 con t ≥ 1; t total ≥ t_requerido(n_pruebas).
- P4: EV/cuota 2-Step (FTMO) > control sin edge; para DZ, que el Sharpe mensual del DARWIN ORB US100 + reversión DZ
  suba ≥ +0,10 al añadirlo, y correlación mensual con ORB y reversión < 0,3.

## Variantes que se mirarán (n_pruebas)
Principal (1) + lookbacks 22 y 34 (2) + versión comprado/vendido (1, solo como diagnóstico) + réplica (1) = **5**
evaluaciones por cada uno de 3 lugares de coste → n_pruebas = 15 (t_requerido ≈ 2,7). Cualquier otra que se mire
se suma aquí. No se añaden filtros para rescatarla.

## Sesgos conocidos de antemano
- Supervivencia: las 20 monedas son grandes hoy, así que comprar-y-mantener sale inflado; por eso el placebo conserva
  la exposición y la réplica usa otro universo (con monedas que cayeron, p. ej. FTT, LUNA no está).
- Solo 4 años de ajuste: potencia baja. Si cae por no significativa se mira la potencia antes de decir "sin ventaja".
