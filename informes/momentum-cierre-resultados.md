# Momentum intradía al cierre en US100: resultados

Fecha: 2026-10-25. Reglas fijadas antes en `informes/momentum-cierre-preregistro.md` (commit
anterior a cualquier resultado). Código: `lab/momentum_cierre.py`. Salida completa:
`informes/momentum-cierre-salida.txt`. Datos: US100.cash M1 de FTMO, 2021-10-05 a 2026-09-29
(1.228 días), y Dukascopy 2018-01 a 2021-09 como comprobación aparte. Nada de esto es una
recomendación de inversión.

## Resumen

| Prueba | Resultado | Veredicto |
| --- | --- | --- |
| 1. Regresión última media hora | Pendiente sobre `r_día` 0,006 (t 0,6), R² 0,07 %; signo acertado 50,4 % | Sin efecto |
| 2. Complementaria 22:30-22:55 | −0,029 R/op con costes, −0,055 R con costes al doble; fuera de muestra −0,10 y +0,02 | No pasa |
| 3. Extensión del ORB a 22:55 | −0,006 R por operación del ORB (t −1,2); peor en las dos ventanas | No pasa |
| 4. Zona de ruido (Zarattini) | +0,12 R/día con costes, +0,10 al doble (t 1,9); fuera de muestra +0,08 y +0,05 al doble | Cumple el listón por la mínima, pero no mejora la cuenta frente a subir el riesgo del ORB; descartada |

## 1. Regresión

En toda la muestra la última media hora no sigue al recorrido del día: pendiente 0,0056 (t de
Newey-West 0,6), R² 0,07 % frente al 2-3 % de los artículos. Con la primera media hora (Gao) la
pendiente es negativa (−0,009, t −0,8), y con solo los 30 minutos de apertura también (−0,011).
Por años solo 2021-2022 tienen pendiente positiva (t 0,9 y 1,4); 2023-2025 son negativos. En días de
volatilidad alta la pendiente es +0,017 (t 1,2) y en los de volatilidad baja −0,024 (t −2,2): el
signo va en la dirección del mecanismo de gamma, pero el efecto es pequeño y no significativo
justo donde debería ser fuerte.

## 2. Estrategia complementaria

Spread real del US100.cash de 22:30 a 23:00: 0,8-0,9 puntos de mediana (P90 1,4), y salta a
2,2 a las 23:01. Con 0,2 puntos de deslizamiento por lado, el coste de ida y vuelta es ~1,2
puntos, un 2 % de 1 R (53 puntos).

| Variante | Costes ×0 | ×1 | ×2 |
| --- | --- | --- | --- |
| `r_día`, salida 22:55 | −0,002 R (t −0,1) | −0,029 (t −1,4) | −0,055 (t −2,7) |
| `r_1ª` (Gao), salida 22:55 | +0,003 (t 0,1) | −0,022 | −0,048 |
| `r_día`, salida 22:59 | | −0,030 | −0,059 |

Antes de costes ya es cero. Por años (×1): 2021 +0,14, 2022 +0,06, 2023 −0,09, 2024 −0,10, 2025
−0,05, 2026 +0,02. Walk-forward 3 + 1: la primera ventana eligió `r_día` con tercil alto de
volatilidad y dio −0,23 R fuera de muestra; la segunda eligió `r_1ª` con tercil alto y dio +0,03
(t 0,4). Sin ajuste: −0,10 (t −2,3) y +0,02. Con Dukascopy 2018-2021: −0,01 R con costes, −0,08 al
doble. Confirma la prueba del 24/10 en el PC: el efecto no existe en el CFD desde 2023.

## 3. Extensión del ORB

De 1.140 operaciones del ORB, 157 (14 %) siguen abiertas a las 22:30 y el 85 % de ellas va a
favor del recorrido del día (el ORB ya es momentum). Alargarlas a las 22:55 resta: las que van a
favor pierden −0,054 R de media en esos 25 minutos y las que van en contra −0,22 R.

| Periodo | Base (22:30) | Extensión | Control (todas a 22:55) |
| --- | --- | --- | --- |
| Todo, costes ×2 | +0,120 R | +0,114 | +0,111 |
| 2024-10 → 2025-09, ×2 | +0,083 | +0,081 | +0,088 |
| 2025-10 → 2026-09, ×2 | +0,157 | +0,143 | +0,136 |

El EA debe seguir cerrando a las 22:30.

## 4. Zona de ruido (Zarattini, Aziz y Barbon)

Parámetros del artículo (14 días, controles cada 30 min, stop en el borde de la zona o el VWAP),
sin tocar, tamaño fijo en R (1 R = 15 % ATR), salida 22:55.

| | Costes ×0 | ×1 | ×2 |
| --- | --- | --- | --- |
| R por día, 2021-10 → 2026-09 | +0,142 (t 2,8) | +0,119 (t 2,3) | +0,096 (t 1,9) |
| Prueba 1, 2024-10 → 2025-09 | | +0,103 (t 0,9) | +0,082 |
| Prueba 2, 2025-10 → 2026-09 | | +0,073 (t 0,6) | +0,053 |
| Dukascopy 2018-01 → 2021-09 | | +0,130 (t 2,1) | +0,070 (t 1,1) |

Opera el 59 % de los días. Por años (×1): 2021 −0,11, 2022 +0,14, 2023 +0,23, 2024 +0,17, 2025
+0,07, 2026 +0,02; se va apagando, igual que el momentum de cierre. Correlación diaria con el ORB:
0,26.

**Colas.** Como el stop solo se revisa cada media hora y puede entrar y darse la vuelta varias
veces, el peor día pierde −7,0 R, el 1 % peor −3,8 R, y 145 días pierden más de 1,5 R. Un stop
fijo intrabarra de 1 R no lo arregla (peor día −7,1 R, P1 −3,0 R) y baja la media a +0,09 al
doble.

**Vecindad** (costes ×2, solo para ver si es casualidad, no para elegir): las 9 combinaciones de
10/14/20 días × 15/30/60 min son positivas en todo el periodo (+0,07 a +0,10 R, t 1,1-2,0), pero en
2024-10 → 2026-09 van de −0,01 a +0,07 (t ≤ 0,8). La del artículo es la mejor de las nueve en
esa ventana.

**Criterio del preregistro.** Positiva al doble de costes en las dos ventanas: sí. La caída
máxima combinada con el ORB sube 12,7 R mientras suma +117 R: sí. t conjunto fuera de muestra
con costes normales > 1: 1,03, por la mínima.

## 5. EV por cuota (FTMO 2-Step 100K, reto 2 %, fondeada 1,5 %, 2021-10 → 2026-09)

Simulador de `cartera/anio_100k.py` (modo Swing), 10.000 años por bloques de 20 días, +0,05 R de
coste por día con operación. Mismo riesgo por unidad de R en las dos estrategias salvo que se
indique.

| Cartera | Neto medio/año | Mediana | P10 | P(neto > 0) | Cuotas/año |
| --- | --- | --- | --- | --- | --- |
| ORB solo | +20.767 € | +18.555 € | −103 € | 90 % | 8,4 |
| ORB + complementaria | +11.232 € | +8.111 € | −5.341 € | 74 % | 11,5 |
| ORB + zona de ruido (×1, mismo tamaño) | +9.256 € | +5.808 € | −11.853 € | 63 % | 24,9 |
| ORB + zona de ruido (×2, a 0,25) | +23.727 € | +21.586 € | +1.240 € | 92 % | 8,8 |
| ORB + zona de ruido (×2, a 0,5) | +23.984 € | +21.395 € | −566 € | 89 % | 12,2 |
| ORB + zona de ruido (×1, a 0,5) | +27.330 € | +24.911 € | +1.379 € | 92 % | 11,5 |
| **Control: ORB con riesgo ×1,25** | **+26.378 €** | +23.766 € | +743 € | 91 % | 11,7 |
| Control: ORB con riesgo ×1,5 | +32.154 € | +28.872 € | +2.307 € | 92 % | 14,1 |

A tamaño completo la zona de ruido hunde la cuenta por las colas (−7 R en un día con el 2 % de
riesgo es −14 %, más que el límite diario). A un cuarto o la mitad del tamaño suma +3.000 a +6.500
€/año, pero subir el riesgo del ORB un 25 % da lo mismo o más con costes al doble, sin un segundo
sistema que mantener. El ORB GER40 sí superaba ese control (informe del 25/10).

## Veredicto

- Momentum de la última media hora (Gao, Baltussen): **descartado**. Cero antes de costes en el
  US100.cash desde 2021 y negativo desde 2023. Es la misma conclusión que la prueba del 24/10 en
  el PC, ahora con regresión, walk-forward, volatilidad y Dukascopy.
- Extensión del ORB hasta las 22:55: **descartada**. Resta en todas las ventanas.
- Zona de ruido de Zarattini: **descartada**. Cumple el listón del informe por la mínima, pero
  fuera de muestra no es significativa al doble de costes (t 0,8), se apaga en 2025-2026, tiene
  colas de −7 R en un día y en EV por cuota no supera a subir el riesgo del ORB. Jorge decidió el
  25/10 que lo que no sirve como estrategia nueva por sí misma se descarta.
