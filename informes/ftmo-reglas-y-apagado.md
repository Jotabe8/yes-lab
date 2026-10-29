# ORB US100: challenge de FTMO con sus reglas reales y criterio de apagado

Prueba simulada, sin dinero real. Nada de esto es una recomendación de inversión.
Código: `lab/ftmo.py` (`python -m lab.ftmo --apagado`). Datos: velas M1 de US100.cash en
FTMO-Demo del 14-09-2021 al 30-09-2026, las mismas de `informes/us100-orb-vwap.md`.

## Qué cambia respecto al Monte Carlo anterior

El Monte Carlo de `us100-orb-vwap.md` usaba las reglas simplificadas del NNFX. Ahora se aplican
las del challenge 2-Step de FTMO y la configuración con la que corre el EA en la demo:

| Regla | Antes | Ahora |
| --- | --- | --- |
| Pérdida diaria (5%) | Resultado cerrado del día | Peor equidad del día, con la pérdida flotante, desde el balance de medianoche |
| Pérdida total (10%) | Desde el máximo alcanzado | Fija: la equidad no puede bajar de 90.000 |
| Días mínimos | No | 4 días con operaciones en cada fase |
| Freno del EA | No | `InpMaxLossPct = 8`: el EA deja de operar al perder un 8% (cuenta como intento perdido) |
| FOMC | No cerraba | Cierra a las 20:55 del servidor los días de FOMC (`InpFomcClose`, activo en la build actual) |
| Muestreo | Días sueltos | Días sueltos, bloques de 20 días seguidos (conserva rachas) y arranque en cada día real |

**Noticias.** En el challenge FTMO no restringe operar con noticias. En la cuenta FTMO estándar
(ya financiada) no se puede abrir ni cerrar en los 2 minutos de antes y después de una noticia
de alto impacto. El ORB entra a las 16:40 (10:10 en Nueva York), lejos de los datos de las
8:30 y las 10:00, y cierra a las 22:30. Lo único que puede caer en la ventana es un stop: de 794
stops en cinco años, 66 (5.7%) saltaron entre las 16:58 y las 17:02 o entre las 20:58 y las
21:02, suponiendo que hubiera noticia todos los días. Son pérdidas, así que no cambian el
resultado, pero en la cuenta financiada conviene la modalidad Swing o comprobarlo con FTMO.

Reglas tomadas de [tradetanto.com](https://tradetanto.com/learn/ftmo-rules-evaluation-process);
conviene confirmarlas en la ayuda oficial de FTMO antes de empezar un challenge. Las del 1-Step
(pérdida diaria 3%, pérdida total del 10% que sube con el máximo balance de cierre y regla del
mejor día del 50%) se han simulado solo como comparación.

## Resultados (100.000, riesgo 0.5%, 5.000 trayectorias)

Las dos fases seguidas (+10% y luego +5%). "Freno" es el freno interno del EA.

| Configuración | Costes | Días sueltos | Bloques de 20 días | Histórico | Mediana hasta pasar |
| --- | --- | --- | --- | --- | --- |
| EA actual (freno 8%) | normales | 66.7% | 70.2% | 76.8% | 106–128 días |
| EA actual (freno 8%) | al doble | 60.2% | 63.4% | 71.5% | 109–131 días |
| Freno al 9% | normales | 71.3% | 75.3% | 80.5% | 110–130 días |
| Freno al 9% | al doble | 65.8% | 69.6% | 76.5% | 116–134 días |
| Sin freno (solo el 10% de FTMO) | normales | 75.5% | 79.5% | 84.0% | 116–132 días |
| 1-Step (una fase, freno 8%) | normales | 70.7% | 73.6% | 77.7% | 57–72 días |

Solo con los 27 meses que no se usaron para elegir la configuración (sep-2021 a dic-2023), el
EA actual pasa el 55.8–72.3% (46.7–58.3% con costes al doble), y con el freno al 9%, el
61.7–75.8%.

Lo que se ve:

1. **La pérdida diaria no limita nada.** El peor día de cinco años, con el flotante, perdió un
   0.75%. Con una operación al día al 0.5%, el 5% de FTMO está muy lejos.
2. **Lo que suspende es la pérdida total, y el freno del EA la adelanta.** Todos los intentos
   perdidos del EA actual acaban en el freno del 8%, no en el límite de FTMO. Sin freno, una
   parte de esas cuentas se recupera: el freno cuesta de 7 a 9 puntos de probabilidad.
3. **Un freno al 9% recupera alrededor de la mitad de esa diferencia** (+3.7 a +5.1 puntos) y deja
   margen: el peor día visto (−0.75%) no lleva de −9% a −10%. Es un cambio de un parámetro
   (`InpMaxLossPct = 9`); no lo he tocado en el EA.
4. **Frente al cálculo anterior** (fase 1 80.7%, dos fases 72.8%), las reglas reales sin freno
   dan algo más (85.4% y 75.5%) porque la caída fija de FTMO es más suave que la medida desde
   el máximo; el freno del EA lo devuelve por debajo (79.0% y 66.7%).
5. **Hace falta paciencia:** la mitad de las cuentas tarda más de 5–6 meses de sesiones en pasar
   las dos fases, y una de cada diez, más de 10–13 meses.

## Criterio de apagado

Con un 29% de operaciones ganadoras, las rachas malas son largas aunque la ventaja exista. Las
bandas salen de un bootstrap por bloques de 10 operaciones de las 1.153 del backtest (R medio
+0.195, cierre antes del FOMC, costes normales). Se cuentan en R, donde 1 R es lo que arriesga
una operación (0.5% = 500 USD en 100.000), y **sobre toda la historia del EA en vivo**, sumando
cuentas y challenges, no por cuenta.

| Señal | Amarilla: revisar, no subir riesgo | Roja: apagar el EA |
| --- | --- | --- |
| Pérdidas seguidas | 21 | 25 |
| Caída desde el máximo | 41 R (20.5%) | 53 R (26.5%) |
| R acumulado tras 20 ops | por debajo de −10.5 R | por debajo de −15.2 R |
| R acumulado tras 50 ops | por debajo de −14.5 R | por debajo de −22.7 R |
| R acumulado tras 100 ops | por debajo de −16.6 R | por debajo de −28.5 R |
| R acumulado tras 250 ops | por debajo de −8.5 R | por debajo de −29.4 R |

Referencia: en 250 operaciones (un año), la racha más larga mediana es de 13 pérdidas y la
caída mediana, de 21.6 R. En la historia real la peor racha fue de 20 y la peor caída, de 31.9 R.

Apagado inmediato, sin esperar a las bandas, si la ejecución se aparta del backtest: entra a
otra hora, se salta días que el backtest opera o el deslizamiento medio pasa del doble del
previsto. Eso lo cubre el diario semanal de la demo.

**Suspender un challenge no es motivo para apagar.** Una cuenta FTMO aguanta 20 R (16 con el
freno del 8%), menos que la caída mediana de un año. Una de cada cuatro o cinco cuentas cae
aunque el EA funcione como en el backtest.

### Cuánto tarda en detectar un EA que ha dejado de funcionar

Probabilidad de que salte la alarma roja según cuál sea la ventaja real:

| Ventaja real | Antes de 100 ops | Antes de 250 | Antes de 500 |
| --- | --- | --- | --- |
| La del backtest (falsa alarma) | 3% | 4% | 8% |
| La mitad (+0.10 R) | 6% | 13% | 26% |
| Ninguna (R medio 0) | 14% | 33% | 60% |
| Perdedor (−0.10 R) | 29% | 62% | 89% |

Con la amarilla las cifras son 11/18/28% de falsas alarmas y 37/63/84% de detección sin
ventaja. Es decir: con esta varianza **ningún criterio distingue un EA roto de una mala racha
en menos de un año**. La roja apaga pronto solo si el EA pierde de forma clara; si la ventaja
se ha ido sin más, lo normal es tardar uno o dos años en saberlo. La amarilla sirve para no
subir el riesgo mientras tanto.

## Limitaciones

- El bootstrap usa los mismos cinco años con los que se validó el EA, y 2024 aporta casi la
  mitad del beneficio (90 R de 225). Si el futuro se parece más a 2021–2023, las bandas son
  optimistas y la probabilidad de pasar baja a la de la tabla de los 27 meses.
- La pérdida flotante sale de velas M1: no ve picos dentro del minuto.
- Las reglas de FTMO salen de una fuente secundaria y pueden cambiar.
