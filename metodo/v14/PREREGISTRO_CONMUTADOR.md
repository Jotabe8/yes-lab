# Preregistro v14b · Sistema propio por régimen de Hurst: "conmutador" (16-11-2026, antes de calcularlo)

Pedido de Jorge tras v14: probar un sistema nuevo basado en Hurst, no solo un filtro.

## Idea y mecanismo
La lectura de libro del exponente de Hurst: con H > 0,5 los movimientos siguen, con H < 0,5 se deshacen.
Sistema: a la apertura propia de cada mercado, tras el rango de 10 min, **si el régimen es persistente se sigue el
cuerpo del rango (ORB), si es antipersistente se va en contra** (misma entrada, mismo stop 0,15 ATR, misma salida).
Se opera **todos los días con señal**, no solo los "en juego", así que es un sistema distinto del v13.

## Aviso de contaminación (honesto)
En v14 ya se vio que el ORB en los días "en juego" gana también en régimen antipersistente (ir en contra ahí
perdería). Lo que NO se ha visto: el resultado en todos los días, que es lo que se prueba aquí (~75 % de los días
no son "en juego"). Ese conocimiento rebaja el prior; no se usa para elegir nada.

## Reglas fijas
- Mercados: GER40, UK100, JP225, XAUUSD (horarios y costes de v13/v14). US100 solo informativo (el v018 ya lo opera).
- Régimen: el de v14 (H ≥ mediana de 250 días previos). Dos variantes: **C1 = H5** (5 sesiones), **C2 = Hhoy**.
- Rendimiento: persistente → r del ORB; antipersistente → r_contra (lado contrario, mismo stop y salida). Coste igual.
- 2012-03 → 2026-11, 1 R por operación, cartera = suma diaria.

## Criterios (todos). Listón por 2 variantes: t ≥ 2,64
1. t neto por operación ≥ 2,64.
2. Placebo: media neta > p99 de 2.000 permutaciones de la etiqueta de régimen dentro de cada mercado
   (mismo nº de días persistentes, asignados al azar).
3. Segunda mitad (desde 2019-07) neto > 0.
4. Costes ×2 neto > 0.
5. ≥ 3 de 4 mercados con neto > 0.
6. Las dos patas aportan: persistente-sigue > 0 y antipersistente-contra > 0 (si una pata es ≤ 0, no es un
   conmutador, es otra cosa).
7. Correlación diaria con v018 < 0,3.
Monte Carlo informativo (bloques de 20 días): P(media ≤ 0), DD p95.
Si no pasa: DESCARTADO, sin rescates (ni otros umbrales, ni solo una pata, ni subconjuntos de mercados).
