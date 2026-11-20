# Preregistro: revisión del filtro de volatilidad p90 del ORB US100 (20-11-2026)

Escrito y subido antes de mirar ningún resultado nuevo. Lo pide Jorge tras 13 días seguidos sin operar
(ATR% en p99-p100).

## Qué se sabe y por qué se revisa
- El filtro se eligió el 25-10 entre 10 variantes (walkforward\RESULTADOS_FILTROS.md, PC): selección 2018-22,
  validación 2023-26, coste extra 0,05 R. Base 6,1 / 27,7 R/año → p90 8,8 / 32,2 R/año.
- Riesgos de esa elección que el método de hoy sí mide: (1) 10 variantes y una sola elegida (selección);
  (2) la mejora de 2018-22 viene sobre todo de 2020 (−26 → −15 R): un solo episodio; (3) los días bloqueados
  vienen en racimos, así que el t por operación exagera (PR #52: t por semana); (4) nunca se probó en 2012-17,
  que no se usó para nada al elegirlo; (5) el ORB en juego (v13) dice lo contrario: el ORB va mejor cuando la
  apertura se mueve más.

## Datos
- Réplica ORB US100 2012-26 por día (`metodo/v14/base/US100_*.csv`, M1 Dukascopy precio medio, rango 10 min,
  vela del rango, stop 0,15 ATR, salida al cierre, sin trailing). Corr 0,74 con el v018 real.
- Coste por operación en R = 0,007 % del precio / (0,15 · ATR) (horquilla FTMO 0,005 % + 0,002 % de
  deslizamiento). Bruto en precio medio, coste después.
- Filtro: ATR% de ayer (atr/px) > percentil 90 de los 252 días previos (mínimo 120), igual que el EA.
- Confirmación secundaria (no decide): serie 2018-26 sin filtro con las reglas exactas del EA si está en el PC.

## Pruebas (3, fijadas ahora)
- **F1. ¿Los días bloqueados pierden?** R neta media de los días con señal que el filtro bloquea.
- **F2. ¿El filtro mejora la cuenta?** Diferencia entre con filtro y sin filtro en R/año, Sharpe de la serie
  diaria y peor DD en R, frente a un placebo: saltar al azar el mismo número de días en racimos de la misma
  longitud (5.000 réplicas, bloques del mismo tamaño que los episodios reales).
- **F3. Pausas largas (el caso de ahora).** R neta media de los días bloqueados que están en un episodio de
  ≥ 10 días hábiles bloqueados seguidos.

Periodos: 2012-17 (nunca usado), 2018-26 (el de la elección) y todo 2012-26. t agrupado por semana
(`embudo.t_agrupado`).

## Regla de decisión (fijada ahora)
Regla de Jorge: no tocar el EA salvo mejora clara. Por tanto:
- **Quitar el filtro** solo si: F1 neta > 0 con t por semana ≥ 2,0 en 2012-26, > 0 en 2012-17 **y** en 2018-26,
  y sin filtro el peor DD no empeora más de un 10 %.
- **Cambiar el tope de 21 días** (operar en pausas largas) solo si F3 > 0 con t por semana ≥ 2,0 y > 0 en los dos
  periodos.
- **Mantener el filtro como está** si F1 ≤ 0 o no llega al listón. Si además F2 no supera el p95 del placebo en
  2012-17, se anota que el filtro **no está demostrado** (se mantiene por la regla de no tocar, no por evidencia),
  y se sigue en real con la cuenta de días bloqueados.
- Ninguna variante nueva del filtro (otros percentiles, otras ventanas) se prueba en este hilo.
