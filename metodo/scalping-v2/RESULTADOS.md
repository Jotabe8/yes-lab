# Scalping con edge: tres familias nuevas (14-11-2026)

**Veredicto: descartado. Ninguna de las 60 casillas pasa** (14 variantes preregistradas × 4 índices en M1,
más 2 variantes con ticks GER40). Ninguna llega a t ≥ 2,4 en la prueba; la mejor tiene t 1,5 y no supera su placebo.
Con los costes de FTMO no hay scalping viable en estos datos: el spread cuesta 0,05-0,07 R por operación y el
bruto medio en la prueba es −0,01 (barridos), +0,03 (desvanecer la apertura, sin réplica) y −0,04 R (redondos).

Preregistro: `PREREGISTRO.md` (escrito antes de abrir datos). Código: `carga.py`, `motor.py`, `familias.py`,
`evaluar.py`, `ticks_ger.py`. Tabla completa: `resultados_m1.csv`.

## Datos
M1 bid + spread real por minuto: US100 (Dukascopy 2018-22 + FTMO 2023-nov 26), US30 y US500 (Dukascopy 2018-26),
GER40 (FTMO nov-21 a oct-26). Ticks bid/ask FTMO de GER40 de 09:00 a 09:07 de Fráncfort (1.135 días, extraídos del
fichero de 2,8 GB del PC). Spread mediano a la apertura: US100 1,1 pt, GER40 0,85-1,05 pt, US30 2,4 pt, US500 0,5 pt.
**Desequilibrio del libro: no se puede probar.** Un CFD no tiene libro y los ticks FTMO solo traen bid/ask.

## Resultados (prueba = 2023-26; GER40 2024-26; R neto con spread real)

| Familia | Qué hace | Mejor casilla en prueba | Ajuste | Placebo p95 | Veredicto |
|---|---|---|---|---|---|
| F1 Barrido de liquidez | Rompe máximo/mínimo de ayer o de la pre-apertura y vuelve a cerrar dentro en ≤ 5 min: entrar contra | US30 nivel de ayer, 2R: +0,133 R, t 1,27 | −0,130 R | 0,156 | No: signo cambia entre periodos y entre índices; en US100 prueba −0,17 a −0,22 R |
| F2 Desvanecer el primer impulso | Si el 1er minuto (o 5 min) sube, corto, salida a 5/15 min | GER40 1 min, 15 min: +0,196 R, t 1,53 | +0,070 R (t 0,34) | 0,311 | No: bajo el placebo, no se replica en US100/US30/US500 (5 min: negativo en los 4) |
| F2 con ticks GER40 | Desvanecer los primeros 30 s, salida a 2/5 min | 2 min: ajuste +0,005, prueba −0,130 R | | | No |
| F3 Números redondos | Primer toque de un múltiplo de 100 (25 en US500): contra, stop 0,1 ATR | Todas negativas, t −0,8 a −5,6 | | | No: el nivel redondo no gana al desplazado un 37 % (US100 prueba −0,089 vs −0,077 R) |

- Casillas con neto > 0 en ajuste y prueba: 3 de 56 (lo esperable por azar). Con coste ×2 ninguna queda bien.
- Paseo aleatorio (velas barajadas dentro del día, US100): ninguna casilla con t ≥ 2,4 positivo; el simulador no
  fabrica ventaja. En F3 el motor es conservador (stop antes que objetivo en la vela de entrada, ≈ −0,03/−0,05 R
  incluso en azar), por eso se juzga contra los niveles desplazados, no contra cero.
- No se abrió la historia larga 2011-17 porque nada pasó la prueba.

## Por qué el scalping no sale aquí (con números)
1. Coste en R. Para que un scalping sea "scalping" el stop tiene que ser corto (el extremo del minuto, 0,1 ATR):
   eso deja el spread en 0,05-0,07 R de media por operación (US100, GER40, US30) y hasta 0,15 R en los días de
   rango pequeño, aun después de quitar las señales con coste > 0,10 R. El ORB paga ≈ 0,02 R porque su stop es ancho.
2. Señal. Antes de costes, ninguna de las tres ideas acierta la dirección de forma estable: bruto en la prueba
   −0,008 R (F1), +0,034 R (F2, solo GER40) y −0,039 R (F3). Haría falta un bruto ≥ 0,15-0,20 R (3 × coste).
3. Lo que queda en la apertura a muy corto plazo ya lo recoge el ORB (continuación a horas), no el desvanecimiento.

## Familias de scalping ya cerradas en el proyecto
NNFX M1/M5/M15 (0/105), coste bajo EMA20 GER40, reversión intradía, VWAP, noticias US100 y shock 08:30,
periodicidad, zona de ruido, scalper nocturno FX y rejillas (v7) y, desde hoy, barridos de liquidez, desvanecer la
apertura (M1 y ticks) y números redondos intradía. Disparador para reabrir: solo con datos nuevos que no existen
aquí (libro real de futuros, p. ej. MNQ con profundidad) y un mecanismo publicado con réplica.

---

# Segunda ronda: scalping a favor de tendencia (14-11-2026)

**Veredicto: descartado, 0/24 casillas** (6 variantes de `PREREGISTRO_TENDENCIA.md` × 4 índices). Señales solo
después de la primera hora (10:30-15:30 NY, 10:00-16:30 Fráncfort), una por día. Código `tendencia.py`, tabla
`resultados_tendencia.csv`.

| Variante | Prueba 2023-26 (neto, t) por índice | Veredicto |
|---|---|---|
| T1 retroceso a EMA20 M5 en día de tendencia (≥ 0,5 ATR), stop 0,15 ATR, 2R | US100 −0,170 (−2,7), GER40 +0,034 (0,4), US30 +0,017 (0,2), US500 −0,054 (−0,7) | No: US100 positivo en ajuste (+0,068) y negativo en prueba |
| T1 igual con salida a 60 min | US100 −0,175 (−3,3) … | No |
| T2 ruptura de microrango (30 min ≤ 0,12 ATR) a favor de la tendencia del día, 2R | US100 +0,088 (1,1), GER40 +0,133 (1,1), US30 −0,017, US500 +0,058 (0,6) | No: positivo en 3 de 4, pero t agrupado ≈ 1,3 y el paseo aleatorio da lo mismo (US100 +0,169, t 1,4) |
| T2 a favor de tendencia, 60 min | GER40 +0,153 (1,5), el resto ≈ 0 | No |
| T2 ruptura en cualquier dirección (2R / 60 min) | todos entre −0,086 y −0,001 | No |

- Correlación diaria con el ORB v018: entre −0,002 y 0,07 en todas las variantes. La descorrelación existe, lo que
  falta es la ventaja.
- El coste aquí ya es bajo (0,01-0,07 R) porque el stop es más ancho que en el scalping clásico; aun así el bruto en
  la prueba no supera 0,03-0,16 R con t < 1,8 en ninguna casilla.
- El paseo aleatorio (velas barajadas dentro del día) conserva el sentido final del día, y "seguir la tendencia del
  día" gana algo incluso ahí. Lo poco positivo de T2 es de ese tamaño, no una ventaja del microrango.
- Ya cerrado antes y no repetido: EMA20/Donchian M1-M15 (oct), seguir choques de 5 min (+0,011 R t 0,69), momentum de
  la última media hora, tendencia de tarde.
