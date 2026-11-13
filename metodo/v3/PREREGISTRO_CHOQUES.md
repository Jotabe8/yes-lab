# Preregistro v3 · Reversión tras choques de 5 minutos (provisión de liquidez) · 13-11-2026

**Familia nueva** (no está en `registro_ideas.csv`): no es dirección a horas fijas ni ruptura de apertura, sino
**provisión de liquidez**. Cuando una orden grande o una cascada de stops mueve el índice en pocos minutos más de
lo que justifica la información, los creadores de mercado absorben el desequilibrio y cobran una reversión parcial
(Grossman-Miller 1988; Nagel 2012, "Evaporating Liquidity"; Heston-Korajczyk-Sadka sobre reversión a minutos).
Quién está obligado: fondos que ejecutan órdenes grandes/stops en cascada. Pago **cóncavo** (al contrario que el
ORB): debería estar descorrelacionado o negativamente correlacionado con el ORB.

## T0 (sin datos)
| Idea | Ops/año | Neto previsto | Años necesarios | Veredicto |
|---|---|---|---|---|
| Estacionalidad de divisas en horario propio (Breedon-Ranaldo 2013), 6 pares | 250 por par | ~1,3 pb publicado ÷2 frente a 0,6 pb de coste; σ 40 pb | > 40 (pares muy correlacionados) | fuera |
| Lead-lag US100 → GER40 tras la apertura de NY | 250 | corr con el ORB alta (misma información) | — | fuera (no descorrelaciona) |
| Rebalanceo de fondos de volatilidad objetivo tras días de estrés | ~15 | | > 50 | fuera |
| **Reversión tras choques de 5 min en índices baratos (US100, US500, US30, GER40)** | ~400-600 agrupados | publicado 10-30 % del choque; choque ≫ horquilla (0,005 %) | ~3-6 | **pasa** |

## Regla (fija antes de ver datos)
- Mercados: US100, US500, US30 (9:30-16:00 NY) y GER40 (9:00-17:30 Fráncfort). M1 bid/ask Dukascopy 2012-2026
  (GER40 desde donde haya datos), **precio medio**.
- Choque: rendimiento de los últimos 5 min |r5| ≥ k·σ5, con σ5 = desviación de los rendimientos de 5 min de las
  20 sesiones anteriores. Solo entre apertura+15 min y cierre−45 min. Tras una operación, 30 min sin nuevas señales.
- Operación: **en contra** del choque, entrada a la apertura del minuto siguiente, stop = tamaño del choque en precio
  (más allá de la entrada), salida a los 30 min o en el stop (comprobado minuto a minuto, huecos a la apertura). R = resultado / stop.
- Coste: horquilla FTMO medida (US100 0,0049 %, GER40 0,0052 %; US500 y US30 sin medir: 0,008 % y 0,005 % supuestos), sin comisión.
- **Principal:** k = 4, salida 30 min, cartera de los 4 mercados (media diaria). Variantes (cuentan): k = 3; salida 60 min.
- **Placebos:** (1) seguir el choque en vez de ir en contra; (2) la misma operación a la misma hora del día anterior
  con el mismo stop (dirección contraria a los 5 min previos de ese día).
- **Pasa si:** t neto ≥ 2,5 en 2012-2026, segunda mitad > 0, costes ×2 > 0, supera a los dos placebos,
  corr diaria con el ORB US100 < 0,3. Si no, se anota y no se rescata.
