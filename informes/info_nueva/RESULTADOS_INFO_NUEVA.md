# Forex y oro con información que no sale del precio

Fecha: 2026-10-25. Esta prueba viene después de unas 80.000 combinaciones NNFX sin edge. La idea es usar datos que no son el precio.

## Datos
- **Tipos de interés** a 3 meses (OECD vía FRED) y a largo plazo. Para EE. UU. se usa el bono a 2 años.
- **Informe COT de la CFTC** (legacy, solo futuros) de 1986 a 2026, para EUR, GBP, JPY, AUD, CAD, NZD, CHF y oro.
- **Cómo se bajan:** con el workflow `.github/workflows/descargar-macro.yml`, porque FRED y la CFTC están bloqueados desde el entorno de Claude. Los ficheros quedan en `datos_macro/`.
- **Precios:** D1 limpios de MT5, y el oro rehecho desde M1.

## Protocolo (fijado antes de ver resultados)
- Ajuste en 2006-2016 y fuera de muestra (OOS) en 2017-2026, al doble de coste.
- Pasa si el t OOS es ≥ 2,5 y el ajuste tiene el mismo signo.
- Los retornos se miden en unidades de volatilidad del periodo.
- **Para no usar datos del futuro:**
  - Los tipos se usan con 2 meses de retraso.
  - El COT (dato del martes) se opera desde la apertura del lunes siguiente a su publicación.
- Para los swaps se supone un coste del bróker del 1,5 % anual, en contra en los dos lados.

## Resultados (al doble de coste)

| Prueba | Ajuste t | OOS t |
|---|---|---|
| Estacionalidad mensual (signo de la media del mes en los 10 años previos) | +0,85 | −1,89 |
| Carry: largo en la divisa de tipo más alto (diferencial > 0,5 pp), con swap | −2,22 | +0,13 |
| Carry, solo precio | −2,52 | −0,21 |
| Cambio del diferencial a 3 meses, en 3 meses (con swap) | −0,98 | −2,46 |
| Cambio del diferencial a largo plazo, en 3 meses (solo precio) | −0,03 | +1,21 |
| COT: seguir el cambio de 1 semana de los especuladores | −1,24 | −2,45 |
| COT: seguir el cambio de 4 semanas | −1,83 | −3,25 |
| COT: seguir el nivel | +0,18 | −2,56 |
| COT: contrario en extremos (z > 1,5 en 3 años) | −3,43 | +0,65 |
| COT: seguir en extremos | +1,86 | −2,87 |

Las versiones contrarias de las reglas de COT, que se miraron después y no estaban registradas, también pierden tras costes. En ellas, el t OOS va de −2,9 a +0,65.

## Veredicto
**Descartado.** Ni el carry, ni el posicionamiento COT, ni la estacionalidad dan ventaja en forex y oro después de costes. El carry, que es la anomalía de divisas más documentada, sale negativo en 2006-2016 por las crisis de 2008 y 2015. En 2017-2026 queda plano.
