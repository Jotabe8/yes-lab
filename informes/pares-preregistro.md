# Valor relativo (pares): reglas fijadas antes de mirar los resultados

Fecha: 2026-10-25. Este archivo se sube al repositorio **antes** de ejecutar la prueba, para que
las reglas no se puedan ajustar a lo que salga. Nada de esto es una recomendación de inversión.

## Por qué esta familia

En el PC de Jorge ya se probaron y descartaron reversión intradía, fade de gap, RSI(2), momentum
de cierre, cambio de mes, trend following en forex y multiactivo, noticias, VWAP, el ORB en 14
mercados y una búsqueda de 25.422 reglas intradía. Ninguna prueba fue de valor relativo. Un par
largo-corto entre mercados muy parecidos es casi neutral a la dirección del mercado, así que
debería correlacionar poco con el ORB del US100 que ya opera en FTMO.

## Datos

Dukascopy D1 (bid) del PC de Jorge, 2010-2025 según el mercado. Solo se usan los cierres para la
señal y las aperturas para ejecutar.

## Pares (lista cerrada, 11)

| Par | A | B |
| --- | --- | --- |
| US500/US100 | USA500IDXUSD | USATECHIDXUSD |
| US500/US30 | USA500IDXUSD | USA30IDXUSD |
| US500/US2000 | USA500IDXUSD | USSC2000IDXUSD |
| GER40/EU50 | DEUIDXEUR | EUSIDXEUR |
| FRA40/EU50 | FRAIDXEUR | EUSIDXEUR |
| GER40/FRA40 | DEUIDXEUR | FRAIDXEUR |
| UK100/EU50 | GBRIDXGBP | EUSIDXEUR |
| Oro/plata | XAUUSD | XAGUSD |
| EURUSD/GBPUSD | EURUSD | GBPUSD |
| AUDUSD/NZDUSD | AUDUSD | NZDUSD |
| Brent/WTI | BRENTCMDUSD | LIGHTCMDUSD |

## Regla

- Diferencial `s = ln A − β·ln B`, con β por mínimos cuadrados sobre los 120 cierres anteriores.
- `z = (s − media) / desviación` de los 60 diferenciales anteriores (calculados con el β de cada día).
- Señal al cierre del día t, ejecución en la apertura de t+1.
- Entrada si |z| > 2: vende el diferencial si z > 2 (corto A, largo B) y lo compra si z < −2.
- Salida si |z| < 0,5, si |z| > 4 (stop) o a los 20 días hábiles.
- Tamaño: las dos patas se ponderan por la inversa de su volatilidad de 60 días y el conjunto se
  escala para que la volatilidad diaria esperada del par sea el 1 % del capital.

## Costes

- Spread por pata en cada entrada y salida: índices 0,02 %, forex 0,01 %, metales 0,03 %,
  petróleo 0,05 % del nocional.
- Financiación CFD: 3 % anual sobre el nocional de cada pata, por día natural mantenido
  (los fines de semana cuentan).
- Prueba de estrés: costes al doble.

## Periodos y criterio de aprobado

- Dentro de muestra: hasta 2019-12-31. Fuera de muestra: 2020-01-01 a 2025-12-31.
- La familia pasa solo si se cumplen las tres condiciones:
  1. Operaciones de todos los pares juntas fuera de muestra: media neta > 0 con t > 2.
  2. Al menos 7 de los 11 pares positivos netos fuera de muestra.
  3. Dentro de muestra también positiva en conjunto.
- Si pasa, los pares positivos dentro de muestra forman la cartera que se mete en el simulador
  de FTMO. Si no pasa, se descarta y no se reajusta.

## Corrección del 2026-10-25, antes de mirar los resultados corregidos

Calcular cada diferencial histórico con su propio β era un error de diseño: como `ln B` vale
en torno a 4-10, un cambio de β de 0,01 mueve el diferencial más que el propio desajuste entre
los dos mercados, y el z mide sobre todo el ruido del β. Lo detectó el test con datos sintéticos
(un diferencial que revierte rápido perdía dinero). La regla correcta, que es la habitual, aplica
el β de hoy a los 60 días anteriores: `s_k = ln A_k − β_t·ln B_k` para k de t−60 a t. El resto
de reglas, pares, costes y criterio no cambian. Se publican los dos resultados.

## Sensibilidad (solo informativa, no sirve para elegir)

Umbral de entrada 1,5 y 2,5; ventana del z 20 y 120. Se publica la tabla completa.
