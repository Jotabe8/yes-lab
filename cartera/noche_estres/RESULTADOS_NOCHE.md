# Prima nocturna tras un día de estrés — PASA el embudo (P0-P4)

Fecha: 2026-10-26. Método: embudo P0-P4 de `metodo/METODO.md`. Preregistro escrito antes de
mirar datos: `cartera/shock0830/PREREGISTRO_NOCHE.md` del PC. n_pruebas contadas: 12.

## Regla

Si una sesión cierra con una caída mayor del **1,5 %** desde su apertura, se compra el índice
al cierre de la sesión y se vende cinco minutos después de la apertura siguiente. Stop fijo del
1 % del precio, sin objetivo. Una operación por mercado y día.

Hipótesis causal: la prima por mantener riesgo de un día para otro se concentra justo cuando la
aversión al riesgo acaba de subir; quien tiene que reducir riesgo (fondos con objetivo de
volatilidad, cuentas con margen) vende en el cierre y paga esa prima al que se la queda.

Mercados (los siete a la vez, no uno elegido): US500, US30, US2000, FRA40, EU50, UK100 y GER40.
Datos M1 bid/ask de Dukascopy 2018-2026 y de FTMO para el GER40.

## Resultados

| Puerta | Resultado |
| --- | --- |
| Frecuencia | 737 operaciones, 85/año (34 noches al año, 2,5 mercados por noche) |
| Coste en R | 0,026 R (spread real de entrada y salida; índices sin comisión en FTMO) |
| Bruto vs coste | +0,183 R = **7,0 × coste** |
| Placebo (noches al azar, mismas salidas) | +0,183 frente al p95 de +0,096 |
| Neto en ajuste 2018-22 | +0,187 R/op, t 3,69 |
| Coste al doble | +0,131 R/op |
| Años positivos | 7 de 9 (negativos 2022 y 2023) |
| Fuera de muestra 2023-26 | +0,076 R/op, n 196, t 1,42 |
| t total | 3,95 frente al 2,64 exigido por 12 pruebas |
| EV/cuota 2-Step (media recortada) | **+5.139 €** al 0,75 % por mercado, frente a **+736 €** del control sin edge |
| Correlación diaria con el ORB US100 | **−0,00** |
| Caída máxima (Monte Carlo, p95) | 10,8 R con el riesgo repartido por noche |

Los siete mercados van en la misma dirección (de +0,089 R el GER40 a +0,237 R el US30) y la
meseta del umbral es limpia y monótona: −1,0 % da +0,126 R con 174 ops/año, −1,5 % da +0,183 R
con 85, −2,0 % da +0,273 R con 42. No hay pico aislado, que es lo que mata a las sobreajustadas.

## Los dos peros, dichos en claro

1. **La financiación de las noches no está en estas cifras** y es lo único que puede tumbarlo.
   Con el stop en el 1 % del precio, cada 0,02 % de coste de financiación por noche son 0,02 R:

   | Financiación por noche | Neto | t | Fuera de muestra |
   | --- | --- | --- | --- |
   | 0,00 % | +0,157 R | 3,95 | +0,076 (t 1,42) |
   | 0,02 % | +0,137 R | 3,45 | +0,056 (t 1,05) |
   | 0,04 % | +0,117 R | 2,94 | +0,036 (t 0,67) |
   | 0,06 % | +0,097 R | 2,44 | +0,016 (t 0,29) |

   Hay que mirar el swap real de FTMO para GER40.cash, US500.cash y compañía. El Strategy Tester
   lo aplica solo, así que el paso P5 contesta esta pregunta directamente.

2. **Es lento.** Con 34 noches al año, la mediana para pasar las dos fases del 2-Step es de
   316 días hábiles al 0,75 % por mercado (192 al 1 %, con menos probabilidad de pasar). No sirve
   como EA único para pasar un reto en semanas; sirve como **segundo EA en la misma cuenta del
   ORB US100**, con el que no correlaciona nada, porque opera de noche y el ORB de día.

## Siguiente paso (P5, le toca a Jorge)

`NocheEstres_v100.mq5` está escrito sobre `metodo/PlantillaPropEA.mq5`: solo se han rellenado
`Senal()` y `Gestionar()`. Hay que copiarlo a `MQL5/Experts`, compilarlo y pasarlo por el
Strategy Tester con ticks reales en 2018-2026, en M1 o M5 y con horas del servidor:

| Entrada | Índices europeos | Índices de EE. UU. |
| --- | --- | --- |
| InpAperturaHora / Min | 10:00 | 16:30 |
| InpEntradaHora / Min | 23:00 | 23:00 |
| InpSalidaHora / Min | 10:10 | 16:35 |
| InpCaidaPct | 1,5 | 1,5 |
| InpStopPct | 1,0 | 1,0 |
| InpRiesgoPct | 0,75 | 0,75 |

Se compara con Python: el EA debe dar aproximadamente 85 operaciones al año repartidas entre
los símbolos y una R media de +0,15 ± 20 %. Si el swap se come más de 0,04 % por noche, cae.
Después, P6: cuatro a ocho semanas en demo de FTMO sin tocar nada.
