# Momentum intradía en BTC: reglas fijadas antes de descargar los datos

Fecha: 2026-10-25. Se sube al repositorio antes de descargar las velas de 30 minutos, así que
nadie ha visto los datos al fijar las reglas. Nada de esto es una recomendación de inversión.

## Hipótesis

Shen, Urquhart y Wang (Financial Review, 2022) encuentran que en Bitcoin el retorno de la
primera media hora del día (UTC) predice el de la última media hora. Es la única idea de la
lista de pendientes de Jorge que no se había probado, y en FTMO el BTC cotiza también en fin de
semana, así que da operaciones los 7 días.

## Datos

Velas de 30 minutos de BTCUSDT en Binance desde 2017-08-17, descargadas por GitHub Actions
(`lab/intradia.py`), porque Binance no es accesible desde el entorno de trabajo ni desde el PC.

## Regla principal

- Día en UTC. `r1` = retorno de 00:00 a 00:30. `rN` = retorno de 23:30 a 24:00.
- Si `r1 > 0`, largo de 23:30 a 24:00; si `r1 < 0`, corto. Una operación al día.
- Resultado por operación = signo(r1) × rN − coste.

## Regla secundaria (del mismo artículo)

Igual, pero la señal es el signo de `r1 + rN-1` (rN-1 = 23:00 a 23:30).

## Costes

0,05 % por operación completa (spread de FTMO en BTCUSD y deslizamiento). Prueba de estrés al
doble. También se publica el resultado bruto.

## Periodos y criterio

- Dentro de muestra: hasta 2020-12-31 (se solapa con el artículo).
- Fuera de muestra: 2021-01-01 hasta el último dato.
- Pasa si, con la regla principal, la media neta fuera de muestra es > 0 con t > 2 y dentro de
  muestra también es positiva. La regla secundaria solo se aprueba si cumple lo mismo; no se
  elige la mejor de las dos a posteriori.
