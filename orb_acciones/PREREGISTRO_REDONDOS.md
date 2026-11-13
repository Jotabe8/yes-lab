# Preregistro: números redondos en índices (Osler 2003/2005)

Mecanismo: los stops se acumulan justo detrás de los niveles redondos y los take-profit justo delante. Al cruzar un redondo saltan los stops y el precio acelera (seguir); al tocarlo desde lejos tiende a rebotar (los TP frenan).
Niveles: US100 múltiplos de 100, US500 de 25, US30 de 250. Placebo: los niveles a mitad de camino (US100 +50, US500 +12,5, US30 +125), menos visibles.
Eventos (9:45-15:30 NY, M1, primer evento por nivel y día):
- CRUCE: el precio medio cierra un minuto ≥ 3 pb más allá del nivel tras venir del otro lado → seguir el cruce, salida a 15 y 30 min.
- TOQUE: el precio llega a ≤ 1 pb del nivel por primera vez en el día → ir en contra, salida a 15 y 30 min.
Medida: rendimiento en pb con entrada en ask/bid y salida en bid/ask (spread real Dukascopy). Ajuste 2018-22, fuera de muestra 2023-26.
Pasa si real − placebo > 0 con t ≥ 2 en 2018-22, neto > 0 y el mismo signo en 2023-26.
