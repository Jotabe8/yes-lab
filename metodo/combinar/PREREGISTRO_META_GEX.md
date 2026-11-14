# Preregistro: meta-etiquetado del ORB US100 con la gamma de los creadores de mercado (14-11-2026)

Escrito y subido ANTES de cruzar el ORB con la GEX. Nadie del proyecto ha mirado esa relación (el hilo de
gamma probó otra cosa: seguir la dirección del día en la última media hora).

## Idea (combinar dos fuentes de información distintas)
- **Primaria con ventaja ya demostrada:** ORB US100 (réplica Python 2012-2026, `datos/orb_us100_2012_2026.csv`,
  columna `neto_ftmo`; contraste con la serie real v018 2018-2026, `datos/serie_v018_be.csv`, columna `R`).
- **Secundaria, información que no sale del precio:** GEX de SqueezeMetrics (`datos/DIX.csv`, cierre del día).
- **Mecanismo:** con gamma negativa los creadores de mercado cubren a favor del movimiento (compran en subidas,
  venden en bajadas) y alargan las rupturas; con gamma muy positiva cubren en contra y "clavan" el precio, lo que
  hace fallar las rupturas. Predicción con signo fijado: **la R del ORB baja cuando la GEX sube.**
- No cambia la entrada ni la salida del ORB: solo el tamaño (meta-etiquetado de López de Prado, versión tamaño).

## Variable
GEX del día hábil anterior al día del ORB, convertida a percentil frente a los 252 días hábiles previos
(sin mirar el futuro). Terciles: bajo (< 1/3), medio, alto (> 2/3). Días sin 252 previos: fuera.

## Pruebas (3, todas cuentan)
1. **P (principal):** tamaño 1,5 / 1,0 / 0,5 en tercil bajo / medio / alto. Se compara la Sharpe por operación
   del ORB con tamaño frente al ORB a tamaño 1 (misma media de exposición ≈ 1).
2. **I1:** diferencia de R media tercil bajo − tercil alto (t de Welch).
3. **I2:** regresión de R sobre el percentil (pendiente, t con errores robustos).

## Listón (todo debe cumplirse para P)
- Mejora de Sharpe con t ≥ 2,4 (diferencia de R entre terciles bajo y alto con t ≥ 2,4 y signo previsto).
- Signo correcto en 2012-2018 y en 2019-2026 por separado.
- Placebo: 1.000 desplazamientos circulares de la serie de GEX (≥ 60 días); la mejora real por encima del p95.
- Réplica sobre la serie real v018 2018-2026: mejora de Sharpe > 0 y diferencia de terciles con el mismo signo.
- Con costes ×2 (restando otra vez `bruto − neto_ftmo`) la mejora sigue > 0.

Potencia (T0): con ~3.100 ops y σ ≈ 2,5 R, cada tercil ~1.030 ops; error de la diferencia ≈ 0,11 R. Solo se
detecta una diferencia de ≥ 0,27 R entre terciles (por ejemplo +0,30 vs +0,03). Es grande, pero es lo que haría
falta para que el tamaño variable compensara en una cuenta prop. Si no pasa: se descarta el meta-etiquetado del
ORB con GEX y no se prueban otros cortes.
