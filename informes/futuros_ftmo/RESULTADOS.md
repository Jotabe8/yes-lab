# Cuentas de futuros de FTMO (FTMO Futures) para los ORB (30/10/2026)

**Conclusión: no compensa frente a las cuentas CFD 2-Step que ya tenemos.** El ORB US100 podría correr en MNQ,
pero rinde menos por cuenta y por euro arriesgado, exige reescribir el EA fuera de MT5 y el GER40 no tiene contrato.
Solo tendría sentido como capacidad extra si algún día se llena el tope de 400K de las cuentas CFD.

## Reglas oficiales (ftmo.com/en/futures)

| | Growth 50K / 100K / 150K | Pro 50K / 100K / 150K |
|---|---|---|
| Precio | 119 / 169 / 229 $ **al mes** mientras dure el reto | 139 / 199 / 269 $ al mes |
| Reset tras quemar | 109 / 159 / 219 $ | 129 / 189 / 259 $ |
| Objetivo (una fase) | 3.000 / 6.000 / 9.000 $ (6 %) | igual |
| Pérdida máxima | 2.000 / 3.500 / 5.000 $, **trailing de cierre de día**, se bloquea en el saldo inicial | 3.000 / 4.500 / 6.000 $, igual |
| Pérdida diaria | reto: ninguna; fondeada: blanda 1/2/3K (cierra el día) | **dura** 1.000 / 1.500 / 2.000 $ en reto y fondeada |
| Consistencia (solo reto) | mejor día ≤ 40 % del beneficio | ≤ 50 % |
| Retiro | tras 4 días ≥ 150/250/300 $; 50 % del beneficio; tope 2.500/3.000/4.000 $ | tras 5 días ≥ 200/300/500 $; hasta 100 %; tope 5.000/6.000/8.000 $ |
| Reparto | 90 % | 90 % |
| Contratos máx. | 5 / 10 / 15 minis (10 micros = 1 mini); en fondeada empieza en 2/4/6 y sube | igual |

Otras reglas: la suscripción se cancela al aprobar; sin días mínimos ni límite de tiempo; sin cuota de activación;
≥ 50 % de cada retiro debe ser beneficio del ciclo; FTMO avisa de que retirar todo en Pro puede tocar la pérdida
máxima (el suelo no baja al retirar). **Cerrar todo antes de las 16:10 ET** (no se mantiene de noche ni el fin de semana).
Noticias permitidas. Trading automático permitido (prohibidos HFT y arbitraje de latencia; EAs de terceros pueden
denegar la fondeada: se pide estrategia única). Copiar entre cuentas propias permitido. Máximo **3 cuentas fondeadas**
a la vez (450K); FTMO dice "across all sizes and product types": falta confirmar si cuenta también las CFD.

**Plataformas: NinjaTrader, Tradovate y TradingView. No hay MT5.** El EA habría que reescribirlo en NinjaScript (C#)
o como estrategia de TradingView con un servicio de puente a la cuenta.

**Contratos**: 30 de CME (NQ/MNQ, ES/MES, YM/MYM, RTY/M2K, NKD, GC/MGC, CL/MCL, divisas, MBT, MET...).
**No hay Eurex: ni FDAX ni FDXM.** El ORB GER40 no puede correr aquí (tampoco lo usamos ya).

**Comisiones**: FTMO 0,50 $/lado minis y 0,20 $/lado micros, más tasas CME y NFA. MNQ ≈ 1,1 $ ida y vuelta + 1 tick
(0,50 $) ≈ 2 $ por contrato frente a ~115 $ de riesgo por MNQ (stop 15 % del ATR diario ≈ 57 puntos) → **≈ 0,02 R**.
En el CFD US100 de FTMO el spread cuesta lo mismo (≈ 0,02-0,03 R) y el ORB es intradía, así que **el swap no
aplica**: los futuros no ahorran costes en esta estrategia.

## Simulación: ORB US100 en MNQ, 1 año (futuros_ftmo.py)

Misma serie y método que dos-orb/ (v018 con BE +2R en fondeada, bloques de 20 días 2022-26, 20.000 MC). Riesgo
por operación = pérdida máxima / K; coste 0,03 R (x2 = 0,06). Al quemar: reset inmediato. En Pro, retirar el
máximo (el colchón tras retirar casi no cambia nada). Mejor K por plan, € netos al año por cuenta:

| Plan | Riesgo/op | Media | Mediana | Año < 0 | Caja p10 | Media costes x2 | Media US100 2018-21 |
|---|---|---|---|---|---|---|---|
| Pro 150K | 1.200 $ (K 5) | 11.000 | 7.200 | 24-27 % | −5.000 | 8.800 | 7.900 |
| Pro 100K | 900 $ | 8.700 | 5.800 | 22-25 % | −3.700 | 6.900 | 6.400 |
| Pro 50K | 600 $ | 6.500 | 4.300 | 21-24 % | −2.550 | 5.200 | 4.900 |
| Growth 150K | 1.000 $ | 5.400 | 2.000 | 42 % | −4.300 | 3.900 | 2.200 |
| Growth 100K | 700 $ | 3.800 | 1.400 | 43 % | −3.150 | 2.800 | 1.600 |
| Growth 50K | 400 $ | 2.600 | 700 | 43 % | −2.200 | 1.800 | 1.100 |

Pro gana claramente a Growth (retira el 100 % y tiene más margen de pérdida); Growth sufre el tope del 50 %.

**Comparación con lo que ya usamos (CFD 2-Step, US100 al 2 %/1,5 %, mismo modelo):**

| Cuenta | Media €/año | Caja p10 | Ratio media / caja |
|---|---|---|---|
| CFD 2-Step 100K (540 €) | 29.300 | −3.800 | 7,7 |
| CFD 2-Step 50K | 14.400 | −2.400 a −3.500 | ~5 |
| CFD 2-Step 10K (89 €) | ~2.700 | ~−600 | ~4,5 |
| **Futuros Pro 150K** | 11.000 | −5.000 | 2,2 |
| **Futuros Pro 50K** | 6.500 | −2.550 | 2,5 |

Con la misma caja en riesgo, el CFD rinde el doble o más. Motivos: pérdida máxima del 4-6 % y trailing (frente a
10 % estática), cuota mensual que se acumula mientras el ORB tarda en llegar al objetivo, y topes por retiro.

## Supuestos que favorecen a los futuros (la realidad sería algo peor)
- La pérdida máxima se comprueba con el cierre de cada operación, no con el flotante intradía.
- Riesgo exacto en $ (con MNQ se redondea a contratos enteros; en 50K son 5 MNQ de ~115 $).
- Precio del MNQ = precio del CFD US100 (diferencia de base y rollos trimestrales ignorados).
- Sin coste de portar el EA ni de validar otra vez en NinjaTrader con datos de NQ.

## Fuentes oficiales
- https://ftmo.com/en/futures/trading-objectives-and-rules/
- https://ftmo.com/en/futures/faq/which-instruments-can-i-trade-with-ftmo-futures/
- https://ftmo.com/en/futures/faq/ftr-which-platforms-can-i-use-for-trading/
- https://ftmo.com/en/futures/faq/ftr-can-i-hold-positions-overnight-or-over-the-weekend/
- https://ftmo.com/en/futures/faq/what-is-the-maximum-number-of-contracts-i-can-trade/
- https://ftmo.com/en/futures/faq/ftr-which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/
- https://ftmo.com/en/futures/forbidden-trading-practices/
- https://ftmo.com/en/futures/faq/how-does-the-payment-for-the-evaluation-work-is-it-one-time-fee-or-a-subscription/
- https://ftmo.com/en/futures/faq/how-do-i-withdraw-my-payout-from-a-sim-funded-account/
- https://promo.ftmo.com/introducing-futures/ (lanzamiento, beta desde finales de agosto de 2026)
