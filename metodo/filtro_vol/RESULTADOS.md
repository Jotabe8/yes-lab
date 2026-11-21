# Revisión del filtro de volatilidad p90 del ORB US100: resultados (20-11-2026)

Preregistro: `PREREGISTRO.md` (subido antes de los datos). Script: `revisar.py`, salida: `salida.txt`.
Réplica ORB US100 2012-26 (M1 Dukascopy, precio medio, sin trailing), coste 0,036 R/op de media. 12 % de los días
bloqueados por el filtro.

| | 2012-17 (nunca usado) | 2018-26 (elección) | 2012-26 |
|---|---|---|---|
| F1 días bloqueados: neto R/op (t semana) | +0,054 (0,23), 107 ops | −0,035 (−0,28), 285 ops | **−0,010 (−0,09)**, 392 ops |
| Días permitidos: neto R/op (t semana) | +0,084 (1,11) | +0,221 (4,12) | +0,170 (3,86) |
| F3 pausas ≥ 10 días: neto R/op (t semana) | +0,081 (0,31), 5 episodios | −0,057 (−0,44), 13 ep. | −0,020 (−0,17), 18 ep. |
| F2 R/año sin → con filtro | 18,0 → 16,9 | 43,8 → 44,9 | 34,0 → 34,3 |
| F2 Sharpe sin → con (p placebo) | 0,54 → 0,53 (0,48) | 1,20 → 1,31 (0,035) | 0,96 → 1,03 (0,06) |
| F2 peor DD sin → con (placebo p5) | 48,5 → **37,6** R (−9,2) | 36,1 → 31,6 R (−6,1) | 48,5 → **37,6** R (−8,6) |

Confirmación con las reglas exactas del EA (PC, walkforward\filtros_resultados.csv, 2018-26, coste extra
0,05 R): los 228 días bloqueados daban ≈ −0,13 R/op. Mismo signo, mismo veredicto.

## Veredicto según la regla preregistrada: **mantener el filtro y el tope de 21 días como están**
- **Quitar el filtro: NO.** Los días bloqueados no tienen ventaja (≈ 0 R neta en 14 años, t −0,09); no hay nada
  que recuperar operándolos. Listón: > 0 con t ≥ 2. Ni se acerca.
- **Cambiar el tope (operar en pausas largas): NO.** En los 18 episodios de ≥ 10 días bloqueados el ORB da −0,02 R.
  La pausa actual no le está quitando dinero esperado al EA.
- **Lo que hace el filtro:** no sube la R por año (+0,3 R/año, dentro del placebo); quita los días en que el ORB
  opera sin ventaja y con toda la varianza. El peor DD baja 11 R (−22 %), más que el p5 del placebo en 2012-17 y en
  todo el periodo. Para una cuenta prop eso es lo que cuenta: misma esperanza, menos riesgo de tocar el límite.
- **Lo que no está demostrado:** que el filtro suba el Sharpe en 2012-17 (p 0,48). La mejora del 25-10 en R/año
  (+2,7 / +4,5) era sobre todo selección y 2020; con la réplica larga es ≈ 0. El beneficio real es el DD.
- Contra el ORB en juego (v13): no hay contradicción. El filtro mira el ATR de los días previos (régimen), el
  ORB en juego mira el rango de la apertura de hoy frente a su media. No se prueba la combinación (preregistro).
- Fallo silencioso en abierto (hallazgo ECC, v019/v021): como los días bloqueados valen ≈ 0 R, operar uno por
  error no cuesta dinero esperado, solo varianza. v022 (falla cerrado) sigue siendo lo correcto en cuentas nuevas,
  pero no es urgente cambiar la v019 de la cuenta real por esto.
