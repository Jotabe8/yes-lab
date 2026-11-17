# v14 · Régimen fractal (Hurst DFA) como selector de los ORB · resultados (16-11-2026)

Preregistro: PREREGISTRO_FRACTALES.md (subido antes de calcular). Datos: M1 Dukascopy bid/ask 2012-26 (workflow
v14-fractales.yml, 74 de 75 mercado-año; falta GER40 2012, igual que en v13). Salida completa: salida_v14.txt.
Estimador comprobado en ruido fraccional (prueba_estimador.txt): recupera H 0,3/0,5/0,7 con sesgo +0,03-0,08
constante; no afecta porque el régimen se mide frente a la mediana propia de los 250 días anteriores.

## Veredicto: NO PASA ninguna de las 4 pruebas → DESCARTADO

| Prueba | Base neto | Persistente neto (t) | Placebo p99 | Sharpe filtrado / base | Mitades | Resultado |
|---|---|---|---|---|---|---|
| A US100 · H 5 sesiones | +0,164 | +0,231 (3,66) | +0,261 | 0,94 / 1,00 | +0,058 / +0,073 | NO (placebo, Sharpe) |
| A US100 · H del día | +0,164 | +0,236 (3,82) | +0,255 | 0,98 / 1,00 | +0,057 / +0,085 | NO (placebo, Sharpe) |
| B en juego · H 5 sesiones | +0,209 | +0,208 (2,17) | +0,364 | 0,55 / 0,74 | −0,042 / +0,033 | NO (5 de 6) |
| B en juego · H del día | +0,212 | +0,150 (1,89) | +0,317 | 0,47 / 0,75 | −0,026 / −0,080 | NO (al revés) |

## Lectura
- **US100:** hay una pista coherente: en días persistentes el ORB gana +0,23 R y en antipersistentes +0,09-0,10,
  en las dos mitades, tercios ordenados (H del día: +0,05 / +0,10 / +0,34) y también en el v018 real 2018-26
  (+0,14-0,16 frente a +0,09-0,11). Pero frente a subconjuntos al azar del mismo tamaño su p-valor es 0,05-0,06
  solo (≈ 0,2 corregido por 4 pruebas), y **quitar la mitad de los días baja el Sharpe** (0,94-0,98 frente a 1,00).
  Como selector no mejora el sistema. Usado como tamaño 1,5/0,5 el Sharpe pasa de 1,00 a 1,03-1,06: ruido.
- **ORB en juego:** no hay efecto, y con H del día va al revés (antipersistente +0,34, persistente +0,15). Que el
  mismo mecanismo dé signo contrario en la otra familia indica que lo del US100 no es una ley general de inercia.
- Informativas: R/S y anchura multifractal Δh tampoco dan un patrón común a las dos bases (R/S en juego al revés;
  Δh US100 al revés de lo que diría "intermitencia = ruptura").

Clase en el registro: **C (potencia/no incremental)**. Sin rescates: no se cambian umbrales, escalas ni ventanas.
El v018 en real no se toca. La lección: el Hurst de corto plazo en M1 está muy cerca de 0,5 en todos los mercados
(media 0,53-0,54) y casi todo su movimiento es ruido de estimación; la inercia que explota el ORB es un efecto de
apertura concreto, no un régimen fractal medible antes.
