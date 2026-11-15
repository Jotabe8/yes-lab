# Búsqueda v7: cambiar la fuente de candidatos (14-11-2026)

## Veredicto
**No hay sistema nuevo.** La fuente alternativa (historiales reales de terceros) apunta a una familia que no se
había probado: la reversión nocturna en cruces FX ("night scalper", y su versión en rejilla). Con preregistro y
16,8 años de M15 bid/ask en 13 pares, el efecto **existe** pero vale ~0,6-1,2 pips por operación, lo mismo que
**solo la comisión** (5 $/lote). Ningún lugar lo hace operable. Familia descartada, sin reserva.

## Qué fuente se eligió y por qué
| Fuente | Valoración |
|---|---|
| (a) Historiales reales de terceros (MQL5, myfxbook, DARWINs) | **Elegida.** Es la única fuente que no se había usado. Los listados son públicos; el detalle de operaciones exige registro. |
| (b) Académicos con réplica independiente | Agotada en este proyecto: los 28 publicados del registro dan 0 éxitos; los efectos con réplica fuera de muestra que caben en una prop (impulso intradía, tendencia, prima nocturna, fin de mes, gotobi, subastas, LETF, gamma, OPEX…) ya están probados. |
| (c) Flujo forzado / microestructura | Probado en v4-v5 (subastas, LETF, gamma, fin de mes, pensiones). Lo que queda (desequilibrios MOC, opciones FX al corte de las 10:00) es dato de pago, y el roll de Goldman exige diferenciales de futuros que no hay en CFD. |

Qué se ve en MQL5 Signals ordenado por antigüedad (14-11-2026, unas 2.700 señales en 56 páginas): los supervivientes largos son
(1) rejillas/promediado en cruces de rango (p. ej. NoPain MT5, solo AUDCAD, 64 % ganadoras, DD 7 % por balance pero 21 % por capital, la firma del promediado),
(2) EAs de oro (ya probados: ORB oro, Bollinger oro) y
(3) scalpers nocturnos. Ancla: Night Hunter Pro All Pairs (IC Markets en real desde 10-2020, 314 semanas, 2.156 operaciones, PF 1,23, Sharpe 0,07, 9 pares).
(1) y (3) usan la misma señal: reversión en horas tranquilas. La rejilla solo cambia la forma de la cola, no la esperanza, así que se probó la señal sin promediar.

## Prueba (PREREGISTRO_NOCHE_FX.md, script noche_fx.py fijado antes de bajar los datos)
Regla: Bollinger 20,2 en M15 (precio medio), barra señal que cierra entre 18:30 y 23:00 NY, se opera en contra a la apertura siguiente,
stop 3 ATR, salida al cruzar la SMA20 o a las 02:00 NY (nunca cruza el cambio de día, así que no paga swap). Coste = horquilla real de Dukascopy más 5 $/lote.
Datos: Dukascopy M15 bid/ask 2010-01 → 2026-10 (workflow v7-noche-fx.yml). Limpieza: fuera las barras de fin de semana y las planas.

| | n/año | bruto R (t) | coste R | neto R (t) | 2010-17 | 2018-26 | 2023-26 |
|---|---|---|---|---|---|---|---|
| Cartera de decisión (9 pares del ancla) | 1.925 | **+0,029 (7,3)** | 0,115 | **−0,086 (−23)** | −0,065 | −0,104 | −0,114 |
| Réplica (AUDNZD NZDCAD GBPCHF EURNZD, no mirados) | 843 | +0,004 (0,7) | 0,131 | −0,127 | −0,111 | −0,140 | −0,176 |
| V2 2,5σ (informativa) | 1.214 | +0,030 (5,7) | 0,109 | −0,079 | | | |
| V3 hasta 01:00 (informativa) | 2.086 | +0,027 (7,2) | 0,117 | −0,090 | | | |
| Placebo de hora 08-12 NY | 1.987 | −0,002 (−0,5) | 0,061 | −0,064 | | | |

- La noche sí tiene algo: el bruto supera al placebo de dirección (+0,029 frente a p95 +0,007) y desaparece a otra hora. El bruto es positivo en 9 de 9 pares de decisión; el mejor par neto es EURUSD (−0,034).
- Pero en pips es diminuto: EURUSD tiene 0,62 pips brutos por operación frente a 0,59 de comisión sola; GBPUSD 0,66 frente a 0,70; AUDCAD 0,62 frente a 0,48 de comisión (2,47 pips de coste total); CHFJPY 1,23 frente a 0,62 (2,26 total).
- **Ni con horquilla cero** queda margen: la comisión sola se lo come. IC Markets cobra 7 $/lote, que es peor. En la réplica ni siquiera hay bruto.
- Correlación diaria con v018: −0,03, que diversificaría si tuviera edge. Peor racha: todos los años son negativos.
- Criterios: no pasan 1, 2, 3, 6 ni 8. Clase B (bruto menor que el coste en cualquier lugar). Se descarta la familia "reversión nocturna FX" en sus dos formas, scalper y rejilla.

## ¿Cómo sobreviven entonces las cuentas de terceros?
Con miles de señales, unas pocas con PF ~1,2 durante 5-6 años es lo que da el azar más la selección. Night Hunter tiene Sharpe por operación de 0,07 y su último mes es negativo (−1,2 %).
Las rejillas enseñan un DD por balance bajo mientras esconden la cola por capital. Esta fuente sirve para saber **qué** se opera,
pero no aporta pruebas de ventaja: hay que medirla igual, y aquí la medida dice que no la hay.

## Conclusión franca sobre "algo debe funcionar"
Ya hay ~75 familias probadas desde 6 fuentes distintas (folklore, gurús, minería, académicos, flujo forzado y ahora historiales reales).
Solo funcionan las aperturas con stop corto en índices baratos (ORB US100, y GER40 al límite). El patrón se repite:
los efectos reales en FX y CFD intradía valen menos de 1 pip o unos pocos pb, y el coste retail es de 1-2 pips o 0,5-1 pb.
**No es que falte buscar mejor: a coste retail, lo que queda sin arbitrar es más pequeño que el coste.** Lo que sí mueve el resultado
es tener más cuentas con el ORB (escalonar firmas, futuros MNQ en Lucid, Darwinex) y no tocar v018.
Disparador de reapertura: ninguno para esta familia (haría falta comisión ≤ 1 $/lote con horquilla ≤ 0,2 pips en cruces, y eso no existe para minoristas).
