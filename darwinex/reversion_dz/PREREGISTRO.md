# Preregistro: reversión de varios días en índices, cuenta de futuros de Darwinex Zero (17-11-2026)

Escrito antes de bajar los datos al contado y antes de calcular nada con esta regla.

## Por qué aquí y no en una prop

En una prop CFD la reversión de varios días muere por el swap (el largo en NDX paga ~6,5 %/año del nominal) y por la
pérdida diaria máxima. En DZ futuros no hay swap ni pérdida máxima y el coste de ES/NQ es ~1 pb. El RSI(2)/reversión
del 25-10 se juzgó en CFD de prop (1-5 pb por operación intradía); **nunca se probó manteniendo varios días en futuros
frente a un placebo que iguale la exposición larga**. Esa es la pregunta: ¿hay ventaja de *momento de entrada* además
de la beta de estar comprado?

Hipótesis causal: las caídas de corto plazo en índices se recuperan en 1-5 sesiones porque quien da liquidez
(creadores de mercado, vendedores de volatilidad cubriéndose, compradores de caídas) cobra una prima por absorber la
venta forzada (márgenes, reequilibrio de volatilidad objetivo, ETF apalancados al cierre). Autocorrelación diaria
negativa documentada en el S&P 500 desde ~2000.

## Regla fija (sin optimizar; parámetros clásicos de la literatura)

- Señal al cierre del día t: IBS = (C − L) / (H − L) < 0,20 **y** C_t < C_{t−1}.
- Entrada: largo al cierre de t. Salida: al cierre del primer día con C > H del día anterior, o al cierre de la 5.ª
  sesión. Sin stop (DZ no tiene pérdida máxima); una posición por mercado.
- Mercados que deciden: ES, NQ, RTY, YM (S&P 500, Nasdaq-100, Russell 2000, Dow; señales sobre el contado ^GSPC,
  ^NDX, ^RUT, ^DJI). Réplica: DAX y Euro Stoxx 50 (FDAX/FESX en DZ; contado ^GDAXI, ^STOXX50E).
- Unidad: R = (salida − entrada) / ATR20 del día de entrada (ATR del contado).

## Costes DZ (por operación ida y vuelta, en puntos del índice)

ES 0,66 (2 ticks + 8 $/50 $) · NQ 0,9 (2 ticks + 8 $/20 $) · RTY 0,36 (2 ticks + 8 $/50 $) · YM 2,2 (2 ticks + 8 $/5 $)
· DAX 2,4 · Euro Stoxx 2,4. Prueba de estrés con coste ×2.

## Periodos

- P1-P2: 2003-01-01 → 2022-12-31. P3: 2023-01-01 → hoy, se abre una sola vez.

## Puertas (todas; la primera que falle descarta)

- **P1:** R bruta media agregada (4 mercados US) ≥ 3 × coste medio; mayor que el p95 de un **placebo de exposición**
  (200 réplicas: mismas duraciones de operación en días de entrada aleatorios del mismo mercado y periodo, lo que
  iguala la beta); bruto > 0 en ≥ 3 de 4 mercados US.
- **P2:** neto y neto ×2 > 0; ≥ 60 % de años positivos; meseta: IBS 0,15 y 0,25, salida máx. 4 y 6 días, todas > 0
  netas; réplica Europa (DAX + Euro Stoxx) neta > 0.
- **P3:** 2023-26 neto > 0 con t ≥ 1; t total ≥ t_requerido(n_pruebas).
- **P4 (DZ):** Sharpe anual de la estrategia (exposición diaria, a igual volatilidad) > Sharpe de comprar y mantener el
  mismo índice; combinada con el ORB US100 (serie_v018_be, Rbe − 0,05, 2018-26) a igual volatilidad mensual:
  correlación mensual < 0,3, Sharpe +0,10 o más y peor DD no peor.
- **Variante corta (informativa, cuenta en n_pruebas):** simétrica (IBS > 0,80 y C > C_{t−1}, corto, salida C < L del
  día anterior o 5 sesiones). No decide.

n_pruebas = 10 (regla principal, 4 meseta, réplica Europa, corto, entrada en la apertura siguiente, coste ×2, OOS)
→ t requerido 2,58.

## Control de tiempo (anticipación)

La señal usa el cierre del contado y se entra a ese cierre: en real se calcula a las 15:58-15:59 NY y se entra al
cierre. Control obligatorio en P2: **entrar en la apertura siguiente** (sin anticipación posible) debe dar bruto > 0
con t ≥ 2. Si la ventaja solo existe entrando exactamente al cierre, se confirma con M1 (señal 15:50) antes de P5.

Lo que no pase, se descarta (no queda en reserva).
