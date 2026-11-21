# v18 — Caída del S&P 500 (16-20 nov 2026) y estrategia para episodios de caída

**Veredicto: la familia "episodios de caída intradía" queda DESCARTADA en P1 (0/2 reglas).** El análisis de la
semana sí deja contexto útil, pero no hay ventaja operable que no tengamos ya (la reversión DZ).

## 1. La semana
| | Lun 16 | Mar 17 | Mié 18 | Jue 19 | Vie 20 | Semana | Desde máximo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S&P 500 | −1,92 % | −1,03 % | −0,23 % | −2,02 % | −3,70 % | **−8,61 %** (6.910) | −11,6 % (máx. 6-10) |
| Nasdaq-100 | −2,67 % | −0,72 % | +0,42 % | −2,21 % | −5,61 % | **−10,43 %** | −19,8 % |
| Dow | −1,41 % | −1,64 % | −1,11 % | −2,19 % | −1,93 % | **−8,02 %** | −11,4 % |

- VIX 19,3 → 35,9 (máx. intradía 40,0); curva invertida (VIX9D 40,7 > VIX 35,9 > VIX3M 30,9). Rango del viernes = 2,6× ATR20.
- Séptima sesión bajista seguida del S&P (racha más larga desde feb-2020); peor semana del Dow desde marzo de 2020.
- **Causas (prensa):** IA. Nvidia publicó el martes (ingresos +103 %, guía 130.000 M$ sobre consenso) y aun así cayó −23 % en la
  semana (−14 % el viernes) con la salida de Huang y una revisión de la SEC sobre contabilidad (según Reuters, sin irregularidades
  probadas). Salida a bolsa de Anthropic el jueves (83 $, abrió a 111,5 $, cerró la semana en 88,9 $) sin rescatar el sector. Fed:
  minutas y Waller apuntan a subida en diciembre (92 % descontado). Restricción de Comercio al cómputo de Nvidia para empresas chinas.
  Semis −17 % (SMH), tecnología −12,5 %, consumo básico −2 % (lo mejor). El 10 años bajó de 5,15 % a 4,91 % (huida a bonos).
- **Intradía (US500 Dukascopy):** toda la caída se hizo **en la sesión al contado**: suma de sesiones 9:30-16:00 −8,6 %, suma
  de noches −0,35 %. Jueves y viernes la caída vino después de las 10:00 (−2,8 % y −3,7 %) y el viernes cerró en el mínimo.
- **Comparación (S&P desde 1950, 5 sesiones ≤ −7 %):** 37 episodios con este. En los 36 anteriores la mediana a 20 sesiones fue
  +3,9 % (75 % positivos, base 62 %), a 60 sesiones +7,8 % (86 %); pero la caída extra media antes del rebote fue −4,8 % y hubo
  colas (2008, 2020: −17/−25 %). Es contexto con n pequeño, no regla. Ya lo explota la reversión DZ (comprar debilidad, varios días).

## 2. La prueba (preregistro en `PREREGISTRO.md`, commit 3c01c36, antes de ver resultados)
Régimen S = US500 ≥ 5 % bajo su máximo de 60 sesiones al cierre de ayer (50 días/año). Barras 30 min Dukascopy 2011-2022,
US500/US100/US30, stop 0,30 ATR20 recorrido barra a barra, coste FTMO 1 pb + 0,5 pb en stop. t agrupado por semana.

| Regla | n | Bruto | Neto | t semana | Placebo p95 | Mercados > 0 | Años > 0 | P1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 corto 10:00→16:00 en S | 1.737 | −0,055 R | −0,078 R | −1,50 | +0,096 | 0/3 | 20 % | NO |
| R2 sigue 9:30-10:00 en S | 1.502 | +0,062 R | +0,039 R | 0,68 | +0,078 | 3/3 | 50 % | NO |

- R1: la semana actual encaja con la hipótesis, pero en 2011-22 las sesiones en régimen de caída **suben** de media (el
  vendedor forzado no se repite; domina el rebote intradía). Vecinos 4 % y 6 %: −0,006 y −0,057 R. El signo opuesto (largo)
  sería elegir tras mirar, t ≈ 1,5, y es la misma idea que la reversión DZ: no se reabre.
- R2: bruto 2,7× coste, por debajo del placebo de lado aleatorio; vecinos t 0,97 y 0,35. Sin ventaja propia (y se solaparía con el ORB).
- No pasa P1 → no se abre 2023-26 ni se miden correlaciones/EV (no hay serie que meter en cartera).

## 3. Qué hacer con episodios así
- Nada nuevo en el EA. El ORB US100 v018 sigue con su filtro de vol p90 (revisado el 20-11: los días bloqueados ≈ 0 R).
- La exposición útil a "después de la caída" ya es la reversión DZ (IBS < 0,2): sus señales de esta semana son exactamente las
  de su regla. Cuidado con la cola: en 2020 y 2008 la caída siguió 15-25 %.
- Familia descartada; no se reabre con otros umbrales (regla del proyecto).

Fuentes de prensa: theglassdesk.substack.com (Weekly Market Review 20-11-2026), schwab.com (Markets' November Nightmare),
journalarta.com (21-11-2026), forbes.com (20-11-2026). Datos: Yahoo y Dukascopy por el workflow `v18-caida.yml`.
