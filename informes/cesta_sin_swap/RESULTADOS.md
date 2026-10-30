# Cesta larga de índices en cuenta sin swap con reglas de E8 Pro (2026-10-30)

**Veredicto.** Aunque E8 no cobrara swap, la cesta no compensa allí. En 3 años, una cuenta de 100K cobra
de media 1.100-1.300 $ (el control sin rendimiento, 500-600 $), con un 45-49 % de probabilidad de pasar.
Descontada la cuota (no publicada; en torno a 500 $ si es como E8 One), quedan unos +200-270 $ al año
por cuenta. Además, E8 permite **una sola estrategia por usuario**, y esa plaza rinde mucho más con el ORB.

## Normas de E8 Pro verificadas

Fuentes: [centro de ayuda de E8](https://intercom.help/e8/en/articles/15274219-e8-pro) y
[tradetanto, 11-ago-2026](https://tradetanto.com/learn/e8-markets-rules).

- Una fase: objetivo del 8 %, pérdida diaria del 2,5 % desde el saldo del día y máxima del 8 % estática.
  Sin límite de tiempo, pero hay que cerrar una operación cada 60 días.
- Solo cuenta un 2 % de beneficio al día; lo que pasa de ahí se retira de la cuenta.
- Retiros diarios con ≥ 1 % de beneficio: se puede pedir el 50 % y se cobra el 80 o el 100 % de esa parte.
  **Tras el primer retiro, el suelo sube al saldo inicial**, con solo la mitad del beneficio como colchón.
- Se permiten fin de semana, noticias y EAs, pero solo **una estrategia por usuario**. No se puede usar un
  EA que usen otros ni cubrir posiciones entre cuentas. Apalancamiento 1:15 en índices.
- **Swap:** no aparece en ninguna fuente oficial. Un agregador dice que E8PRO v2 es sin swap de serie, pero
  otro lo da como complemento de pago y el anuncio de junio de 2026 habla solo de forex y cripto.
  **No está confirmado para índices.**

## Simulación

`cesta_e8.py` y `umbral.py`: 6 índices de contado (US500, US100, US30, GER40, UK100, JP225), largos solo
por encima de la SMA200, pesos inversos a la volatilidad, volatilidad objetivo del 5 al 15 %, spread al
rebalancear, sin swap y sin dividendos. Monte Carlo de 3 años con bloques de 20 días (2005-2026,
2.000-3.000 caminos) y las reglas de arriba. El control es la misma serie con media 0.

| Volatilidad | Primer retiro | Pasa | Cobro medio en 3 años | Control |
| --- | --- | --- | --- | --- |
| 5 % | al 1 % | 49 % | 615 $ | 335 $ |
| 7,5 % | al 1 % | 45 % | 619 $ | 367 $ |
| 7,5 % | **al 8 %** | 45 % | **1.303 $** | 601 $ |
| 5 % | al 4 % | 49 % | 1.145 $ | 507 $ |
| 10 % | al 8 % | 34 % | 770 $ | 414 $ |

La mediana de cobro es 0 $ en todos los casos: más de la mitad de las cuentas nunca cobran. Retirar
pronto es lo peor, porque el suelo sube al saldo inicial con muy poco colchón.

## Qué haría

- En E8, la plaza de "una estrategia" es para el ORB.
- Para la cesta, la única opción razonable es FTMO, que admite varias estrategias y ya tiene el EA probado.
  Antes hay que preguntar a su soporte si la cuenta sin swap cubre índices, qué cuesta, y si una cesta
  siempre comprada choca con la norma de "apuestas de un solo lado". Con esa respuesta se simula con sus reglas.
