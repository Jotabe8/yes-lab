# Preregistro v5-1: régimen de gamma de los creadores de mercado y última media hora (14-11-2026)

Escrito y subido al repositorio **antes de descargar los datos de gamma** (SqueezeMetrics `DIX.csv`) y antes de
construir las barras 2018-2026 de US500. Nadie del proyecto ha mirado nunca la gamma. La última media hora sin
condición sí se miró (25-10-2026, US100 FTMO 2021-26: sin efecto), y con la volatilidad como sustituto de la
gamma salió el signo esperado pero débil (+0,017, t 1,2). Eso es todo lo visto.

## Pagador y mecanismo

Los creadores de mercado de opciones sobre el S&P 500 cubren su delta. Cuando su gamma neta es **negativa**, tienen
que comprar cuando el mercado sube y vender cuando baja, y la mayor parte de esa cobertura se hace al final de la
sesión. Ese flujo forzado empuja la última media hora en la dirección del día. Cuando su gamma es positiva hacen lo
contrario y frenan el movimiento. Fuente: Baltussen, Da, Lammers y Martens (2021), *Hedging demand and market intraday
momentum*, Journal of Financial Economics; también Barbon y Buraschi (2021), *Gamma fragility*. El pagador cubre por
obligación de gestión de riesgo, no por opinión, y seguirá haciéndolo mientras exista el mercado de opciones.

Dato nuevo para el proyecto: la exposición gamma estimada (GEX) diaria publicada gratis por SqueezeMetrics desde
2011. Es una estimación de modelo (supone que los creadores están cortos de calls y largos de puts de los clientes),
no la posición real.

## Regla principal (una sola)

- Instrumento: US500 (CFD del S&P 500; datos Dukascopy M1 bid/ask, precio medio, barras de 30 min en hora NY).
- Muestra: todos los días con barras completas desde 2011-09 hasta el último día descargado.
- Condición: **GEX del último día publicado anterior a la fecha de la operación < 0** (sin mirar el dato del mismo día).
- Señal: signo de `ln(cierre 15:30 / apertura 9:30)`.
- Operación: entrar a la apertura de la barra 15:30 en esa dirección, salir al cierre de la barra (15:59). Sin stop.
  No se solapa con el ORB US100, que cierra a las 15:30 NY.
- Resultado en puntos básicos (pb) de precio. Coste base 1,0 pb ida y vuelta (horquilla FTMO en índices US
  0,5-0,8 pb + deslizamiento); costes ×2 = 2,0 pb.

## Listón (todo debe cumplirse)

1. t neto (costes ×1) ≥ 2,4.
2. Media neta > 0 en la segunda mitad de la muestra (por fechas).
3. Media con costes ×2 > 0.
4. Placebo: media bruta por encima del p95 de 2.000 selecciones al azar del mismo número de días entre todos los
   días (misma regla de señal, sin condición de gamma).
5. Cola: con la serie diaria a volatilidad anual 15 %, caída máxima < 3 × beneficio medio anual.
6. Réplica en US100 (mismo día, misma condición SPX-GEX): media neta > 0 y t ≥ 1,5. US100 no se mira hasta que US500
   esté calculado.

Antes de mirar: con σ ≈ 17,5 pb por media hora (US500 2011-17) y unos 25-60 días de gamma negativa por año, 14 años
detectan con 80 % de potencia una media neta de unos 2-3 pb. Si la gamma negativa tiene menos de 150 días en total,
la prueba se declara **sin potencia** (clase C) y no se rescata cambiando el umbral.

## Variantes informativas (no pueden aprobar nada)

- I1: GEX en el 20 % más bajo de los 252 días anteriores (percentil móvil, sin mirar el futuro), misma señal.
- I2: GEX en el 20 % más alto → **contra** la señal (frenado por gamma positiva).
- Informativo también: media en días de GEX ≥ 0 con la regla principal (debe ser menor), 2023-2026 por separado (era
  de opciones de vencimiento diario), correlación diaria con la serie del ORB US100 v018.

## Si pasa / si no pasa

Si pasa: reserva hacia delante en papel desde hoy (mínimo 40 operaciones nuevas) y P4 (EV por cuota) antes de
escribir MQL5. Si no pasa: se anota en `metodo/v3/registro_ideas.csv` con su clase y no se prueban otras ventanas,
umbrales ni mercados elegidos después.
