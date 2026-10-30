# Cómo vencer al spread de un CFD de prop (2026-10-30)

Medido con las M1 del PC (2023-26; US100, GER40 y USOIL con spread de FTMO, el resto Dukascopy).
**Coste relativo** = spread ida y vuelta / movimiento medio absoluto entre entrada y salida. Es la parte
del movimiento que una señal tiene que acertar de más solo para empatar. Script `mapa_coste.py`, tabla `mapa_coste.csv`.

## 1. El coste depende de dónde y cuándo, no del CFD en sí

| Mercado | Spread (pb) | Coste rel. 30 min | 2 h | Hasta el cierre | 1 día |
|---|---|---|---|---|---|
| US100 (apertura NY) | 0,54 | 1,7 % | 1,1 % | 0,7 % | 0,8 % |
| GER40 (apertura Fráncfort) | 0,53 | 2,8 % | 1,8 % | 0,9 % | 1,1 % |
| US30 (apertura NY) | 0,59 | 2,7 % | 1,7 % | 1,2 % | 1,3 % |
| US500 | 0,88 | 4,7 % | 2,6 % | 1,6 % | 1,5 % |
| Oro | 1,6 | 8 % | 4,1 % | 2,0 % | 1,9 % |
| UK100 / FRA40 | 1,3-1,4 | 8-9 % | 5 % | 2,4-2,7 % | 2-4 % |
| Petróleo | 4,1 | 10 % | 5,2 % | 1,7 % | 1,9 % |
| EU50 | 4,7 | 24 % | 15 % | 7 % | 7 % |
| GER40 de noche (01-08 h servidor) | — | — | 17-46 % | — | — |

Mejor ventana por mercado. Fuera de ella el coste se multiplica: US100 a 2 h pasa de 1,1 % en la apertura
a 5-8 % de madrugada. El GER40 nocturno cuesta 15-25 veces más que en su apertura.

## 2. Qué significa
- En US100, US30 y GER40, durante la sesión de contado, el spread es solo el 1-2 % del movimiento.
  **Allí el spread no es lo que mata las ideas: lo que falta es una señal que acierte la dirección.**
  El scalping, la periodicidad, el momentum de cierre o el EMA20 se probaron con estos costes y su
  bruto ya era ≈ 0 o negativo.
- Donde el spread sí decide: M1-M5, fuera de la sesión de contado, EU50, UK100, forex (spread + comisión),
  oro y petróleo a plazos cortos, y todo lo que mantiene posiciones de noche (el swap de FTMO en índices,
  ~10 %/año del nominal, cuesta ≈ 3 % del movimiento diario por cada noche, más que el spread).
- Las pruebas con diarios de Yahoo usaban un coste supuesto de 0,02 % (EE. UU.) y 0,04 % (Europa). Para
  US100, US30 y GER40 el real es 0,005-0,008 %, de 3 a 5 veces menos. No cambia veredictos (esas ideas
  tenían menos de 40 operaciones al año o no superaban el placebo), pero la lección "los efectos publicados
  ganan lo mismo que cuesta un CFD" solo vale para mercados caros, plazos cortos o posiciones de noche.

## 3. Reglas prácticas
1. **Operar solo US100, US30 o GER40 y en su sesión de contado** (coste rel. ≤ 3 %). Evitar EU50, UK100,
   Asia y horas nocturnas.
2. **Mantener la operación horas, no minutos**: de 30 min a cierre el coste relativo baja a la mitad o un tercio.
   Cerrar antes del cierre del día (sin swap).
3. **Stop amplio frente al spread**: coste en R = spread / stop. Con stop ≥ 0,25 ATR diario en US100 el coste
   es ≈ 0,02 R; con stops de pocos puntos en M1 sube a 0,3-0,4 R (lo que mató el scalping).
4. **Pocas operaciones, cada una con recorrido**: cada operación paga un spread entero; dividir la misma
   exposición en muchas entradas solo multiplica el coste.
5. **Órdenes**: en un CFD las limitadas y stop también pagan el spread (se ejecutan con bid/ask). Solo
   ahorran el deslizamiento de las órdenes a mercado en momentos rápidos. No son una forma de vencer al spread.
6. **Cuenta sin swap** solo si la idea necesita varios días: el coste diario baja a ~1 % del movimiento.
7. **Firma**: medir el spread real de cada firma en MT5 antes de comprar (exportar ticks de US100/GER40 en la
   apertura). FTMO ya está entre las más baratas en índices y no cobra comisión en ellos.

## 4. Criterio para ideas futuras
Una idea solo merece P1 si su señal puede explicar al menos 3 veces el coste relativo de su ventana:
en US100 a la apertura, acertar de más ≈ 3-5 % del movimiento; en oro o FRA40, ≈ 15-25 %; en EU50 o de noche,
inviable. El ORB cumple porque opera en la ventana más barata, con recorrido hasta horas después y stop amplio.
