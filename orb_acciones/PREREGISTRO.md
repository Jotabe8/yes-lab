# Preregistro: ORB de 5 minutos en acciones "en juego" (13-11-2026)

Idea: Zarattini, Barbon y Aziz (2024), "A Profitable Day Trading Strategy for the U.S. Equity Market".
Familia nueva en el proyecto: el ORB solo se ha probado en índices, oro y forex; el gap de resultados
en acciones se probó a 5 sesiones en D1, no intradía.

Hipótesis causal: el día que una acción tiene noticia propia (resultados, guía, rebaja), el volumen de
apertura se dispara y el flujo informado sigue empujando en la dirección de los primeros minutos;
la liquidez de esos días hace que el spread sea pequeño frente al recorrido.

Reglas (fijas, sin optimizar):
- Universo: acciones US disponibles como CFD en FTMO (o su equivalente en el MT5 de laboratorio).
- Rango: vela de 5 min 9:30-9:35 NY. Volumen relativo (VR) = volumen de ticks 9:30-9:35 / media de ese
  mismo tramo en los 14 días previos.
- "En juego": VR >= 2, como mucho las 5 de mayor VR del día.
- Dirección: signo de la vela de 5 min (sin operación si cierre = apertura).
- Entrada: orden stop en el máximo (largos) o mínimo (cortos) del rango, válida 9:35-10:30 NY.
- Stop: A) 10 % del ATR(14) diario (paper); B) otro extremo del rango.
- Salida: 15:55 NY. Coste: spread ask-bid real + comisión FTMO de acciones.
- Variantes miradas: 2 stops x 2 filtros (VR >= 2 / sin filtro) = 4.

Periodo: ajuste 2018-2022 (o desde que haya datos); fuera de muestra 2023-2026, abierto una vez.
Placebo: mismos días, acciones y salidas con dirección aleatoria (200 réplicas).
Puertas: P1 bruto >= 3x coste y > p95 del placebo; P2 neto con costes x2 > 0, >= 60 % años +;
P3 OOS > 0 con t >= 1, PBO <= 50 %; P4 EV/cuota 2-Step > control y corr diaria con ORB US100 < 0,3.
