# Preregistro: scalping a favor de tendencia (14-11-2026, antes de ver datos)

Pregunta de Jorge: "¿Y un scalping trend following?". Ya probado y NO se repite: retroceso a EMA20 y ruptura
Donchian 20 con EMA200 en M1/M5/M15 con gestión NNFX (oct, 0/105; Donchian US100 M15 murió tras 2022), seguir
choques de 5 min (v3: +0,011 R t 0,69), momentum de la última media hora y tendencia de tarde convexa, ORB (en vivo).
Aquí solo variantes fuera de la hora del ORB y con stop más ancho que el spread.

## Comunes
- US100, US30, US500 (2018-26) y GER40 FTMO (2021-26), M1 bid + spread real; mismo motor que `PREREGISTRO.md`.
- Ventana de señal: 10:30-15:30 NY (US) y 10:00-16:30 Fráncfort (GER40): después de la primera hora.
- Tendencia del día = signo de (cierre del minuto − apertura de la sesión), y solo si |distancia| ≥ 0,5 ATR(20) diario.
- Una operación por día y variante (la primera señal). Se salta si spread / riesgo > 0,10 R. Cierre como tarde al
  final de la sesión.
- Pasa si: neto > 0 en ajuste y prueba, t ≥ 2,4 en prueba, coste ×2 > 0, > p95 del placebo (dirección aleatoria,
  20 rep.), mismo signo bruto en ≥ 2 de los otros 3 índices, y correlación diaria con el ORB v018 < 0,3.

## T1. Retroceso dentro de la tendencia del día (2 variantes)
- Velas M5 con EMA20 de M5. Día en tendencia alcista: el mínimo de la vela M5 toca la EMA20 y la vela cierra por
  encima y alcista → largo a la apertura siguiente (simétrico en cortos).
- Stop 0,15 ATR diario. Salida: (a) objetivo 2 R; (b) por tiempo a 60 min.

## T2. Ruptura de microrango (4 variantes)
- Microrango = últimos 30 minutos con rango ≤ 0,12 ATR diario. Ruptura = cierre M1 fuera del microrango; entrada a
  la apertura siguiente. Stop = el otro lado del microrango + 1 spread.
- (a) solo a favor de la tendencia del día; (b) en cualquier dirección. Salida: objetivo 2 R o por tiempo a 60 min.

Total: 6 variantes × 4 índices. Nada se añade después de ver resultados.
