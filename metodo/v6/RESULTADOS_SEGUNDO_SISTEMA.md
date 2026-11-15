# Segundo sistema para diversificar el ORB US100 (14-11-2026) — no hay

**Respuesta corta.** La única pista viva (ORB de ETH a las 9:30 NY) se cierra. Sí existe un sitio con el coste
pedido (Lighter, cuenta estándar, 0 % de comisión), pero la réplica preregistrada en 8 criptomonedas no miradas
no pasa: cartera +0,04 R/día, t 0,76, 2024-26 negativa. Y ETH con datos de otra fuente (Binance) se queda en
t 1,96 con 0,03 % de coste (2024-26 t 1,08). No hay segundo sistema. La diversificación posible hoy es de
cuentas y de tiempo, no de estrategia (sección 3).

Archivos: `PREREGISTRO_ORB_CRIPTO_REPLICA.md` (escrito antes de bajar datos), `orb_cripto_replica.py`,
workflow `v6-orb-cripto-replica.yml`, series en `replica/`, `replica_analisis.py` → `replica_salida.txt`.

## 1. Dónde operar ETH a ≤ 0,04 % ida y vuelta

| Sitio | Coste i/v aprox. | ¿Llega? | Problema |
|---|---|---|---|
| **Lighter, cuenta estándar** (DEX) | 0 % comisión + horquilla y latencia de 300 ms ≈ 0,02-0,03 % | **sí** | No autorizado en el EEE, sin KYC, capital propio, bot en Python (no MT5) |
| MEXC (0 % maker / 0,02 % taker) | ~0,045 % | justo | Sin licencia UE, riesgo de contraparte |
| Binance USDC-M (0 / 0,04 %) | ~0,08 % | no | Salida de la UE |
| Kraken UE, OKX X-Perps (0,02 / 0,05 %) | ~0,10 % | no | Regulados, pero caros. En España la CNMV trata los perpetuos como CFD (2:1) |
| Lighter premium, Hyperliquid | 0,056 % / 0,09 % | no | — |
| CME ETH estándar (50 ETH) | ~0,02-0,03 % | sí | ~800 $ de riesgo por contrato: no cabe en ninguna prop ni en el presupuesto |
| CME micro MET (0,1) / Spot-Quoted QETH (0,2) | 0,2-1 % | no | La tasa fija se come el nominal pequeño |
| Prop cripto (HyroTrader en Bybit, Breakout en Kraken) | ≥ 0,10 % | no | Comisión de la plataforma |
| Prop de futuros (Topstep, Lucid) | — | no | Topstep solo MBT/MET; Lucid sin cripto |

Conclusión: solo Lighter llega, y fuera de cualquier prop. Por eso la prueba tenía que ser dura.

## 2. Réplica preregistrada (8 monedas no miradas, Binance M1, 2021-03 → 2026-10, coste 0,03 %)

| Criterio | Resultado | ¿Pasa? |
|---|---|---|
| 1. Neto cartera t ≥ 2,4 | +0,039 R/día, t 0,76 | no |
| 2. 2024-26 > 0 y ambas mitades > 0 | 2024-26 −0,016; 2ª mitad −0,016 | no |
| 3. Costes ×2 > 0 | −0,006 | no |
| 4. H1 (lado) t ≥ 2 o H2 (sesión 9:30 vs 01:00) t ≥ 2 | H1 t 0,59; H2 t 1,03 | no |
| 5. ≥ 5 de 8 monedas con neto > 0 | 6 de 8 (pero ninguna con t > 1,4) | sí |
| 6. Correlación con v018 < 0,3 | 0,09 | sí |

Por año (cartera neta, R): 2021 −1, 2022 +37, 2023 +33, 2024 +3, 2025 +6, 2026 −20. El efecto fue de 2022-23
y se apagó. ETH con datos de Binance: 0,02 % → t 2,21 (2024-26 t 1,26); 0,03 % → t 1,96; 0,04 % → t 1,71.
BTC: t 1,48 con 0,03 %. La versión de Dukascopy era la más favorable de las dos fuentes.

Veredicto: clase D (cae fuera de muestra). Disparador de ETH cerrado; familia ORB cripto cerrada.

## 3. Qué diversificación sí es posible sin un edge nuevo

Serie v018 neta (2018-26): 37 % de meses negativos, peor mes −12 R, peor trimestre −15 R, peor bache −33 R
y 319 operaciones (más de un año) sin máximos. Con todas las cuentas en el mismo EA, eso pasa a la vez en
todas. Lo que sí reduce el daño:

1. **Escalonar compras.** Comprar retos de uno en uno, cada 1-2 meses (como ya dice el plan), en vez de
   varios a la vez. En un bache, unas cuentas están en reto y otras ya fondeadas con colchón: no se pierden
   todas por el mismo tramo. Es diversificación en el tiempo, no de mercado.
2. **Riesgo distinto según la fase.** Más riesgo en el reto (la cuota es la única pérdida) y menos en la
   fondeada con poco colchón. Así el mismo mal mes quema retos baratos y no fondeadas.
3. **Retirar en cuanto se pueda** y dejar el colchón mínimo. El beneficio retirado ya no lo toca el siguiente bache.
4. **Varias firmas** (FTMO, The5ers, Lucid, Darwinex). No reduce el riesgo de mercado, pero sí el de
   impago, cambio de reglas o cierre de una firma.
5. **Presupuesto para el bache.** Contar con perder 3-4 cuotas seguidas sin cambiar nada del EA.

Lo que no diversifica: variantes del mismo ORB (mismos días), GER40 (sin ventaja), cripto (sin ventaja).

## 4. Ideas nuevas que quedan

No tengo ninguna que cumpla las 6 condiciones del estudio "desde cero" con datos gratis. Las dos con mejor
mecanismo necesitan un dato que no tenemos o tienen poca potencia:
- **Desequilibrios de cierre del NYSE/Nasdaq (MOC):** el pagador está claro (fondos indexados que tienen que
  comprar o vender al cierre), pero el dato se publica a las 15:50 y es de pago (Nasdaq/NYSE). La "última
  media hora" sin ese dato ya se descartó.
- **Ventana de recompras de acciones:** las empresas compran durante el día cuando no están en periodo de
  bloqueo. Calendario de resultados gratis, pero el efecto esperado es de 1-3 pb al día frente a 0,5-1 pb de coste
  y σ ~100 pb → harían falta más de 50 años de datos para llegar a t 2,4 (falla el triaje T0).

Recomendación: cerrar la búsqueda de un 2º sistema hasta que aparezca un dato nuevo (por ejemplo, si Jorge
quiere pagar los datos MOC) y dedicar el esfuerzo al reparto del ORB entre firmas y en el tiempo.
