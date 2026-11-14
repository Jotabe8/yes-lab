# Dónde operar barato las ventajas reales (14-11-2026)

**Respuesta corta.** Ningún bróker ni firma convierte en rentable una ventaja que hoy no lo sea. Para casi todas,
el problema no era solo el coste: la ventaja se apagó en 2024-26 (JP225, BTC) o es demasiado pequeña (víspera,
gotobi). La única que sigue viva en 2024-26 es el **ORB de ETH**, y no hay ningún sitio que la ofrezca a ≤ 0,04 %
ida y vuelta (lo más barato encontrado cuesta ~0,09 %). **El ORB US100 sigue siendo el único sistema.** El coste
nunca fue su problema (0,02-0,03 R en todas partes). Lo que importa es dónde ponerlo con 100-200 €/mes.

Reglas sin tocar. Series ya guardadas. Script `recalculo.py` → `recalculo.csv` y `recalculo_salida.txt`;
cripto `cripto_umbral_salida.txt`; prop de futuros `sim_futuros_prop.py` → `sim_futuros_prop_salida.txt`.

## 1. Estrategia × sitio (neto por operación con el coste de cada sitio)

Listón v3: t neto ≥ 2,4, 2024-26 > 0 y costes ×2 > 0.

| Estrategia | Sitio | Coste ida y vuelta | Neto R | t | Neto 2024-26 | R/año | ¿Pasa? |
|---|---|---|---|---|---|---|---|
| Gotobi USDJPY (08:00→09:55 JST) | FTMO (medido) | 1,52 pips | +0,023 | 1,1 | +0,03 | 1,7 | no |
| | **IBKR spot** (0,2 pb/lado) | ~0,9 pips (horquilla 0,3 supuesta) | +0,059 | 2,9 | +0,05 | 4,2 | justo; ×2 ≈ 0 |
| | IBKR con horquilla 0,5 | 1,1 pips | +0,047 | 2,3 | +0,04 | 3,4 | no |
| | Darwinex (0,005 %) | ~1,25 pips | +0,039 | 1,9 | +0,04 | 2,8 | no |
| | Tickmill / IC cTrader / IC MT5 / Pepperstone | 1,3-1,45 pips | +0,03 | 1,3-1,8 | +0,03 | 2-2,6 | no |
| | Futuros CME 6J | ~2 pips (el tick ya vale 1,1) | −0,005 | — | — | — | no |
| ORB JP225 (apertura Tokio) | FTMO CFD (medido 0,0157 %) | 9,4 pts | +0,077 | 1,5 | +0,01 | 18 | no |
| | CFD ECN (IC/Pepperstone) | ~9 pts | +0,081 | 1,6 | +0,01 | 19 | no |
| | CME NKD (IBKR o Topstep) / OSE mini | 5,9-6,6 pts (0,010-0,011 %) | +0,10-0,11 | 2,0-2,15 | +0,03 | 24-25 | no |
| ORB BTC 9:30 NY | **Pepperstone CFD** (sin comisión, horquilla media ago-26 15 $ = 0,022 %) | 0,022 % | +0,184 | 2,5 | +0,08 | 44 | **no: 2025 −4 R, 2026 +2,5 R** |
| | FTMO CFD / Darwinex CFD / perpetuos | 0,07-0,12 % | −0,04 a +0,08 | <1,2 | <0 | — | no |
| ORB ETH 9:30 NY | Umbral que haría falta | ≤ 0,04 % | +0,18 | 2,5 | +0,15 | 43 | **sí, si existiera** |
| | FTMO CFD (medido) | 0,09 % | +0,092 | 1,3 | +0,06 | 22 | no |
| | Pepperstone (2 $ a ~2.100 $ = 0,1 %) / Darwinex 0,12 % / perpetuos taker 0,09 % | 0,09-0,12 % | +0,04-0,09 | <1,3 | — | — | no |
| Víspera de festivo US (US100/US500/US30, 9:30→cierre, 2011-26) | CFD FTMO o futuros | 0,002-0,006 % | +0,08 | 1,8 | ≈ 0 | **0,7** | no: 9 ops/año |
| ORB US100 | cualquier sitio (CFD FTMO, NQ/MNQ, NDX Darwinex) | 0,02-0,03 R | +0,15-0,24 | — | — | ~25 | **sí (ya corre)** |

Lo que enseña la tabla:
- **Gotobi**: solo IBKR (forex al contado, no CFD) se acerca al disparador de 0,8 pips, y solo si su horquilla a
  las 08:00 JST es ≤ 0,3 pips. Aun así son unos 4 R/año con dinero propio, sin MT5 (API de IBKR) y con costes ×2
  plano. Con 5.000 € al 1 % serían unos 200 €/año. No compensa el trabajo.
- **JP225**: los futuros bajan el coste a 0,010 %, pero el bruto de 2024-26 es solo ~+0,05 R. Neto 2024-26 ≈ +0,03. Muerto.
- **BTC**: Pepperstone cumple el disparador de coste (≈ 0,02 %), pero la ventaja desapareció: 2025 −0,02 R/op,
  2026 +0,01 en ~430 operaciones, con máximo bache de −40 R. El sitio llega cuando la ventaja ya se fue.
- **ETH**: es la única ventaja que se mantiene en 2024-26, pero ETH es caro en todas partes (0,09-0,12 %). Nuevo
  disparador: un sitio con ETH a ≤ 0,04 % total y apalancamiento ≥ 1:2 a las 9:30-16:00 NY.
- **Víspera**: el problema no es el coste sino el número de operaciones (9 al año, +0,7 R/año) y 2024-26 ≈ 0.
- Carry cripto y subastas del Tesoro: ningún sitio cambia nada (se apagaron en origen). Darwinex tiene ZN pero el
  efecto murió en 2016.

## 2. Otras firmas para el ORB US100 (lo único operable)

Coste US100/NQ/MNQ: 0,02-0,03 R en todas. Lo que cambia son las reglas de pago. Monte Carlo de 1 año, serie v018
con BE +2R, coste 0,03 R, mejor riesgo por plan, € netos por cuenta:

| Cuenta | Cuota | Media €/año | Mediana | Año < 0 | Caja p10 | Media prudente (2018-21) | Media/caja |
|---|---|---|---|---|---|---|---|
| **FTMO CFD 2-Step 10K** (referencia, MT5) | 89 € una vez | 2.750 | — | — | −620 | — | **4,4** |
| **Lucid Flex 50K** (MNQ, sin cuota mensual) | ~80 $ una vez (115 $ sin cupón) | 2.540 | 1.640 | 27 % | −720 | 1.500 | 3,5 |
| Topstep 50K | 49 $/mes + 149 $ activación | 4.800 | 2.170 | 34 % | −1.825 | 3.860 | 2,6 |
| FTMO Futures Pro 50K | 139 $/mes | 6.330 | 4.390 | 21 % | −2.450 | 4.870 | 2,6 |
| Topstep 150K | 149 $/mes + 149 $ | 6.800 | 3.600 | 33 % | −3.430 | 4.380 | 2,0 |
| Take Profit Trader 50K | 170 $/mes + 130 $ | 2.640 | 1.600 | 37 % | −3.630 | 2.240 | 0,7 |
| Lucid Flex 100K / 150K | 150 / 226 $ | 2.840 / 3.500 | 1.410 / 2.060 | 33-35 % | −1.650 / −2.030 | ~1.300-1.500 | 1,7 |

- Todas las de futuros permiten bots según el seguimiento de mayo-nov 2026 (Lucid lo dice expresamente; prohíben
  HFT, cobertura y microscalping), pero **ninguna tiene MT5**: el EA habría que portarlo a NinjaTrader/Tradovate o
  conectarlo con un puente tipo TradersPost. Confirmar en cada web antes de pagar, y que aceptan residentes en España.
- Por euro arriesgado, la FTMO CFD 10K sigue siendo la mejor. Lucid Flex 50K es la única de futuros que entra en el
  presupuesto sin cuota mensual y con caja parecida. Topstep da más media pero con el triple de caja en riesgo.
- Firmas CFD con MT5 ya revisadas (memoria): The5ers y E8 (una estrategia por usuario) y FundingPips (10K ≈ FTMO 10K
  por euro). Son la 2ª firma más sencilla porque el EA no cambia.

## 3. Darwinex: qué encaja

- **Encaja: ORB US100**, en la cuenta CFD (NDX, 0,9 pts + 2,75 $/orden ≈ 0,02 R) o en la de futuros (NQ, 4 $/orden
  ≈ 0,01 R). Es lo que ya está en el plan (DARWIN del ORB, permanente +10 % si va bien).
- **No encaja nada más**: gotobi en el CFD de Darwinex (~1,25 pips) t 1,9; en 6J, negativo. No hay Nikkei en
  Darwinex. Cripto CFD al 0,05 %/orden se come el ORB de BTC y ETH. La víspera en futuros sale barata pero da 0,7 R al
  año. Subastas (ZN), apagadas desde 2016.

## 4. Recomendación con 100-200 €/mes

1. Mantener el plan: Black Friday de FTMO, 2-Step Swing 10K con el ORB US100. Es lo que más rinde por euro.
2. 2ª firma, en enero: una CFD con MT5 (FundingPips 10K o The5ers), porque usa el mismo EA. Si se quiere repartir
   riesgo de impago fuera del mundo CFD, la alternativa es **Lucid Flex 50K** (~80 $ una vez, +2.500 €/año de media,
   caja −720), pero exige portar el EA a NinjaTrader.
3. Darwinex: solo el DARWIN del ORB US100, como ya estaba previsto.
4. No abrir cuenta propia en IBKR ni en Pepperstone para gotobi o BTC: no compensa (gotobi ~200 €/año con 5.000 €; BTC
   sin ventaja desde 2025).
5. Disparadores que quedan: **ETH a ≤ 0,04 % total** en algún sitio con apalancamiento ≥ 1:2; **gotobi ≤ 0,8 pips**
   (IBKR es el candidato: medir su horquilla a las 23:00 UTC con la cuenta demo, que es gratis).

## Fuentes y supuestos

- Comisiones oficiales: IBKR forex 0,20 pb/lado, mín. 2 $ (interactivebrokers.co.uk); IBKR futuros MNQ 0,25 $, estándar
  0,85 $ + tasas CME (ES ejemplo 2,24 $/lado); IBKR no ofrece futuros cripto a clientes minoristas en Europa;
  IC Markets EU Raw 3,5 $/lado MT, 3 $ cTrader (icmarkets.eu); Darwinex 0,005 % del nominal ida y vuelta
  (help.darwinex.com); Pepperstone sin comisión en cripto, horquilla media ago-2026 BTC 15,15 / ETH 2,01
  (pepperstone.com, entidad AE: comprobar la de la UE).
- Prop de futuros: Topstep y Take Profit Trader (luxalgo, reglas verificadas 15-01-2026), Lucid (tradetanto 04-11-2026,
  precios propfirmmap jun-2026), política de bots (algopropfirms, mayo 2026).
- Supuestos: horquilla USDJPY a las 08:00 JST de 0,3-0,5 pips en brókers ECN/IBKR (no medida); JP225 CFD ECN 9 pts;
  USDJPY a 150 y Nikkei a 60.000 para pasar comisiones fijas a pips/%.
