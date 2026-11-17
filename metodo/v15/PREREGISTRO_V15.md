# Preregistro v15 · Otras matemáticas: cointegración con Kalman y procesos de Hawkes · 16-11-2026

Escrito **antes de descargar los datos** (M1 bid/ask Dukascopy 2012-2026, precio medio). Jorge pidió (16-11)
"otras estrategias matemáticas" aparte de los fractales (v14, descartados). Revisado el registro de ideas
(`v3/registro_ideas.csv`) y la memoria: ninguna de estas dos familias se ha probado. Se descartan en T0, sin datos:

| Herramienta | Idea | Por qué no se prueba |
|---|---|---|
| HMM / cambio de régimen | régimen como selector del ORB o conmutador seguir/contra | es el mismo diseño que v14 (Hurst) y v14b, ya descartados; los filtros del ORB no mejoran |
| Entropía de permutación / información | entropía previa como filtro del ORB | igual que arriba: filtro del ORB |
| Espectral / wavelets | ciclos intradía | periodicidad intradía ya descartada (PR #14) |
| Valores extremos (GPD) | revertir colas extremas | "choques de 5 min" (v3) ya dio que los choques no revierten; las colas extremas (flash crash) son < 10/año y el llenado en CFD es irreal |
| Recurrencia / análogos k-NN | forma de la mañana → tarde | sin pagador; ML LightGBM intradía ya dio −0,07 R |
| Cambio de punto (CUSUM) | detectar inicio de tendencia | momentum de media sesión y tendencia de tarde ya descartados; M1 H ≈ 0,53 (v14) |

## H1 · Valor relativo intradía entre índices US con beta de Kalman

**Mecanismo.** US500, US100 y US30 comparten casi todo su riesgo. Durante la sesión, flujos que no traen
información (creación/reembolso de ETF sectoriales como QQQ/DIA, rebalanceos, una acción de precio alto que pesa
mucho en el Dow) separan un índice de los otros. Los arbitrajistas estadísticos y los creadores de mercado de ETF
cobran por absorberlo (Avellaneda-Lee 2010; Nagel 2012). Si el pagador existe, la separación acumulada desde la
apertura revierte en parte antes del cierre. Pago cóncavo y neutral al mercado: debería estar descorrelacionado del ORB.

**Regla (fija).**
- Pares: US500/US100, US500/US30, US100/US30 (A/B en ese orden). Velas de 5 min en precio medio, 9:30-16:00 NY.
- Beta: filtro de Kalman sobre rendimientos de 5 min, `rA_t = β_t·rB_t + e_t`, β paseo aleatorio.
  Varianza del estado q = 1e-4·(var(e) / var(rB)) por vela; varianza de observación = var(e) de las 20 sesiones previas
  (con la β de entonces). Arranca con MCO de las 20 primeras sesiones. Solo velas de sesión (la noche no entra).
- Residuo acumulado del día desde las 9:35: `S_k = Σ (rA − β_{t−1}·rB)` con la β que había antes de cada vela.
  z_k = S_k / (σ_e·√k), σ_e = desviación de e de las 20 sesiones previas.
- Entrada: primera vela entre 10:00 y 15:00 con |z| ≥ 2 → **en contra** (si S > 0, corto A y largo β·B), a precio de
  cierre de esa vela (medio). Una operación por par y día.
- Stop: S se aleja otra vez lo mismo que en la entrada (S = 2·S_entrada). Objetivo: S = 0. Si no, cierre 15:55.
  Comprobado vela a vela con cierres de 5 min; huecos dentro de la vela al cierre de la vela (sin máximo/mínimo del spread).
- R = (S_entrada − S_salida)·signo / |S_entrada|. Coste en R = (c_A + |β|·c_B) / |S_entrada|, con horquillas FTMO
  US100 0,0049 %, US500 0,008 % (supuesta), US30 0,005 % (supuesta).
- **Principal:** z = 2, cartera de los 3 pares (media diaria de R). Variantes (cuentan): z = 2,5; salida solo a las 15:55.
- **Placebos:** (1) seguir la separación (mismo stop y objetivo invertidos: stop en S = 0, objetivo 2·S); (2) misma
  hora del día anterior con el mismo tamaño de stop, en contra del signo de S que había en ese día a esa hora.

## H2 · Saltos endógenos frente a exógenos (proceso de Hawkes)

**Mecanismo.** Bouchaud y colaboradores (Joulin et al. 2008; Hardiman-Bouchaud 2013) y Filimonov-Sornette (2012)
miden que la mayoría de los saltos intradía no traen noticia: son endógenos, la propia actividad los excita (cascadas de
stops, algoritmos que siguen a otros). Un salto exógeno (noticia) cambia el valor y se queda; uno endógeno es presión
sin información y debería revertir. v3 vio que el conjunto de choques de 5 min sigue un poco (+0,03 R bruto): eso es
compatible con una mezcla de las dos clases que se anulan. La clasificación se fija antes, con un modelo ajustado
en el año anterior: **no es un rescate de v3 porque cada clase va en un sentido distinto y se prueba la diferencia**.

**Regla (fija).**
- Mercados y sesiones de v3: US100, US500, US30 (9:30-16:00 NY) y GER40 (9:00-17:30 Fráncfort). M1 precio medio.
- Saltos (eventos del Hawkes): minutos con |r1| / σ1(m) ≥ 4, con σ1(m) = desviación de r1 en ese minuto del día
  (ventana ±5 min) de las 20 sesiones previas (quita la forma en U de la volatilidad).
- Hawkes univariante de núcleo exponencial λ(t) = μ + Σ α·β·e^{−β(t−t_i)} (t en minutos de sesión, se reinicia cada
  día), ajustado por máxima verosimilitud en los saltos del **año natural anterior** de ese mercado.
- Choque (como v3): |r5| ≥ 4·σ5, entre apertura+15 y cierre−45, 30 min sin señales tras una operación.
- Cuota endógena del choque: η = 1 − μ / λ(t₀⁻), con λ evaluada justo antes del inicio de los 5 min del choque
  (solo saltos anteriores). **Endógeno si η ≥ 0,5 → en contra; exógeno si η < 0,5 → a favor.**
- Entrada a la apertura del minuto siguiente; stop = tamaño del choque; salida a los 30 min o en el stop, minuto a minuto,
  huecos a la apertura (motor de v3). Coste: horquillas de v3 (GER40 0,0052 %).
- **Principal:** cartera de los 4 mercados, regla combinada. Variantes (cuentan): umbral η 0,3/0,7 (lo intermedio no se opera); salida 60 min.
- **Placebos:** (1) clasificación al revés (endógeno a favor, exógeno en contra); (2) 200 asignaciones aleatorias
  de la clase con la misma proporción por mercado y año (p95).

## Puertas (las dos hipótesis)

Pasa solo si, sobre 2012-2026 (US30/US500/GER40 desde donde haya datos):
1. t neto de la principal ≥ 2,5 (3 variantes + 2 placebos por hipótesis).
2. Segunda mitad > 0 y costes ×2 > 0.
3. Supera a los dos placebos (placebo 2 de H2: por encima de su p95).
4. Al menos 2 de los 3 pares (H1) / 3 de 4 mercados (H2) con neto > 0.
5. Corr diaria con el ORB US100 v018 < 0,3.
6. Motor: la misma regla sobre velas barajadas (`sinteticos.py`, 10 réplicas) da |t| < 2.

Si no pasa, se anota la clase (A sin bruto, B bruto < coste, C sin potencia, D cae en la 2.ª mitad) y **no se rescata**.
Si pasa, sigue P4 (EV 2-Step frente al control) y P5 (MQL5 + Strategy Tester con ticks FTMO).
