# Preregistro v14 · Régimen fractal (Hurst) como selector de los ORB probados (16-11-2026, antes de ver los datos)

## Qué se pide y por qué así
Jorge: "usa matemática de fractales para encontrar un sistema con ventaja basado en los que ya están probados".
Revisado: en el registro de ideas, DIARIO y carpetas no hay ninguna prueba de Hurst, DFA, R/S ni multifractalidad
(nunca se probó). Los dos sistemas con ventaja son de **inercia**: el ORB US100 (v018) y el ORB en juego v13
(GER40/UK100/JP225/oro, rango de apertura ≥ 1,5× media). La matemática fractal mide justo eso: el exponente de
Hurst H > 0,5 indica incrementos persistentes (lo que sube tiende a seguir subiendo), H < 0,5 antipersistentes.
**Hipótesis:** el ORB gana más en los días en que el mercado está en régimen persistente (H alto) y poco o nada en
régimen antipersistente. Si es cierto, un ORB filtrado (o con tamaño según H) sería un sistema nuevo mejor que el
base. Riesgo conocido: H es información del propio precio, y los filtros de precio sobre el v018 (hueco,
extensiones, variantes, GEX) no mejoraron. Por eso se exige mejora en Sharpe y frente a placebo, no solo t.

## Medidas (precio medio M1 Dukascopy bid/ask, solo datos anteriores a la entrada del minuto 10)
- **V1 (principal) H5:** Hurst por DFA-1 de los rendimientos logarítmicos M1 de las **5 sesiones anteriores**
  (ventana de la sesión propia de cada mercado, la misma de v13; se concatenan los rendimientos dentro de cada
  sesión, sin el salto entre sesiones). Escalas 4, 6, 8, 12, 16, 24, 32, 48, 64 minutos; H = pendiente de
  log F(s) frente a log s.
- **V2 Hhoy:** Hurst por DFA-1 de los **390 rendimientos M1 anteriores a la entrada** (incluye el rango de apertura
  y la pre-sesión del mismo día). Escalas 4, 6, 8, 12, 16, 24, 32.
- Informativas (no deciden): Hurst R/S de las 5 sesiones (Anis-Lloyd no; R/S clásico) y anchura multifractal
  MFDFA Δh = h(q=−2) − h(q=+2) de las 5 sesiones.
- Comprobación del estimador antes de usarlo: paseo aleatorio → H ≈ 0,5; ruido fraccional con H = 0,3 y 0,7
  → recupera el valor (±0,05).

**Régimen persistente** (por mercado, sin mirar el futuro): H del día ≥ mediana de H de los 250 días anteriores
del mismo mercado (mínimo 60 días; antes, no hay régimen y el día no cuenta en ninguna prueba).

## Sistemas base (sin tocar sus reglas; resultados por día de metodo/v13/datos, copiados en v14/base)
- **A. ORB US100** (réplica v13: 9:30-15:55 NY, rango 10 min, cuerpo ≥ 10 %, stop 0,15 ATR, 2012-26). Decide.
  Informativo: serie real del v018 (serie_v018_be.csv, 2018-26) con el mismo filtro.
- **B. ORB en juego** cartera MT5 = GER40, UK100, JP225, XAUUSD con RRANGO ≥ 1,5 (USOIL fuera, coste real).
Costes por operación los de v13 (% del precio): US100 0,0049; GER40 0,0052; UK100 0,0079; JP225 0,0157; oro 0,0110.

## Pruebas: 2 medidas × 2 bases = 4. Una prueba pasa si cumple TODO:
1. t neto por operación del ORB filtrado (solo días persistentes) ≥ 2,4 en 2012-2026.
2. **Placebo:** media neta filtrada > percentil 99 (corregido por 4 pruebas) de 2.000 subconjuntos al azar del mismo
   tamaño por mercado, sacados de los días del sistema base con régimen definido.
3. Mejora (media filtrada − media base) > 0 en las dos mitades (corte 2019-07-01).
4. Costes ×2: neto filtrado > 0.
5. Sharpe anual de la serie diaria filtrada > Sharpe de la base en el mismo periodo (operar la mitad de días tiene
   que compensar; si no, no es un sistema mejor).
6. Tercio alto de H con media neta > tercio bajo.
Monte Carlo informativo (bloques de 20 días): P(media ≤ 0), DD p95 en R. Informativo: tamaño 1,5 R en días
persistentes / 0,5 R en antipersistentes (Sharpe frente a la base).

Si ninguna pasa: DESCARTADO (clase en el registro), sin cambiar umbrales, escalas ni ventanas después de ver datos.
Si alguna pasa: es una versión nueva (el EA en real no se toca), P4-P6 del embudo y decide Jorge.
