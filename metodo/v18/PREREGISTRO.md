# v18 — Episodios de caída en índices US (preregistro, 21-11-2026, antes de mirar resultados)

Pedido de Jorge (21-11-2026): analizar la caída del S&P 500 de la semana del 16-20 nov 2026 y estudiar si hay
una estrategia con ventaja en US500/US100/US30 en este tipo de episodios.

## Qué ya está probado (no se repite)
- Reversión de varios días tras cierre débil (IBS < 0,2): ya es la pata de Darwinex Zero (PR #51). No se duplica.
- Momentum de última media hora (oct), tarde convexa (nov) y gamma negativa (GEX < 0, última media hora, PR #28): descartados.
  En episodios de caída la gamma suele ser negativa, así que el "momentum de cierre en días de pánico" ya está probado.
- Prima nocturna tras día de estrés (oct, fallo del stop corregido): descartada. Con FTMO el swap mata lo nocturno.
- Fade del hueco intradía (oct): descartado sin condición.

## Hipótesis causal
En un episodio de caída (corrección en marcha) los vendedores obligados (fondos de volatilidad objetivo, paridad
de riesgo, CTA, ajustes de margen) reducen exposición **durante la sesión al contado**, cuando hay liquidez, y la
compra de rebote llega fuera de horario (la "prima nocturna" se concentra en la noche). Si es así:
- **R1 (sesión bajista):** en régimen de caída, la sesión 10:00 → 16:00 NY tiene deriva negativa → corto.
- **R2 (sigue la primera media hora):** en régimen de caída, la dirección de 9:30-10:00 continúa hasta el cierre
  (desequilibrio de órdenes que se reparte en la sesión). Lado = signo de la barra 9:30-10:00.

## Régimen de caída (S), conocido antes de la apertura del día d
Cierre de US500 en d−1 ≤ 0,95 × máximo de cierres de US500 de las 60 sesiones anteriores (incluida d−1).
Mismo régimen para los tres mercados (es un estado del mercado US, no de cada índice).

## Datos y simulación
- Barras de 30 min de precio medio Dukascopy (bid/ask) 9:30-16:00 NY: `orb_acciones/indices_2012/` (2011-17) y
  `orb_acciones/indices/` (2018-nov 2026). US500, US100, US30. Régimen con los cierres 16:00 de esas barras.
- Entrada al cierre de la barra 0 (10:00). Salida al cierre de la barra 12 (16:00) o en el stop.
- Stop = 0,30 × ATR20 diario (en puntos, de días anteriores), recorrido barra a barra (máximo/mínimo de cada barra
  de 30 min posterior a la entrada); se llena en el precio del stop. R = movimiento / stop.
- Coste: horquilla FTMO real US100 0,0049 % por lado redondeado a **1,0 pb ida y vuelta** para los tres
  (+ 0,5 pb de deslizamiento en el stop). Coste ×2 en P2. Se informa también la horquilla Dukascopy medida.

## Pruebas (n_pruebas = 4: R1, R2, cada una con y sin stop; la principal es CON stop)
Ajuste 2011-2022 (los tres mercados agrupados, t agrupado por semana). Fuera de muestra 2023-2026 se abre una vez.

| Puerta | Pasa si |
| --- | --- |
| T0 | ≥ 40 ops/año por mercado en S; bruto ≥ 3 × coste |
| P1 | neto > 0 con t agrupado ≥ 2,4; los 3 mercados > 0; supera el p95 de un placebo: R1 = la misma operación corta en un subconjunto aleatorio de días (mismo nº, fuera de S) → mide si S aporta algo; R2 = lado aleatorio en los mismos días (200 réplicas) |
| P2 | neto con coste ×2 > 0; ≥ 60 % de años con días S positivos; régimen vecino (umbral 4 % y 6 %) conserva ≥ la mitad |
| P3 | 2023-26 neto > 0 y t ≥ 1; t total 2011-26 ≥ t requerido para 4 pruebas (2,50) |
| P4 | correlación diaria con ORB US100 v018 < 0,3 y con la reversión DZ < 0,3 (|corr|); no puede ser la reversión DZ con otro nombre |

Se juzga la **familia** (R1 y R2 en los tres mercados), no la mejor variante. Si ninguna pasa: DESCARTADA la
familia "episodios de caída intradía" y no se reabre con otros umbrales.

## Análisis descriptivo de la semana (no es una prueba)
Magnitud, días, volatilidad (VIX, rango intradía en ATR), comportamiento por media hora de cada día, comparación
con correcciones anteriores del S&P 500 (desde 1950: caídas ≥ 5 % en ≤ 10 sesiones) y qué pasó 5/20/60 sesiones
después (solo contexto: n pequeño, no es regla).
