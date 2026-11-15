# ORB para Lucid Flex 50K y elección de la segunda firma MT5 (14-11-2026)

## Resumen

- **Lucid**: el ORB v018 ya está portado a NinjaTrader 8 (`ORB_MNQ_Lucid.cs`, micros MNQ). Su réplica en Python cuadra con la
  serie v018 día a día: **mismos días en el 96,9 %**, correlación de R **0,999**, mismo signo en el 99,9 %. Falta que lo
  compiles en tu NinjaTrader y pases el backtest de validación (pasos en `LEEME_NINJATRADER.md`).
- Con **350 $ de riesgo** (2 a 5 micros según el día) una LucidFlex 50K da **≈ +2.900 €/año de media** (mediana +1.950 €,
  24 % de años negativos, caja en el 10 % peor −640 €). Es lo mismo que una FTMO 2-Step 10K (+2.740 €, caja −620 €).
- **Segunda firma MT5 en enero: The5ers High Stakes 10K.** Son casi las mismas reglas que FTMO 2-Step, cuesta 78 $ (≈ 70 €)
  frente a 89 €, el apalancamiento en índices (1:25) deja usar el 2 % y su norma de noticias solo prohíbe poner órdenes
  2 minutos antes y después. Da **≈ +2.840 €/año** por cuenta frente a **≈ +2.280 €** de FundingPips 10K.
- **Black Friday**: hecho el cambio pendiente del EA (CSV con el nº de cuenta) y los .set de 10K (`black-friday-ea/`).

## 1. Reglas de Lucid comprobadas en su web oficial (support.lucidtrading.com, 14-11-2026)

| Regla | LucidFlex 50K |
|---|---|
| Objetivo del reto | 3.000 $ |
| Pérdida máxima (MLL) | 2.000 $, arrastre al cierre del día; se bloquea en 50.100 $ cuando el saldo de cierre pasa de 52.100 $; al pedir retiro pasa a 50.100 $ |
| Pérdida diaria | opcional y blanda (al tocarla se bloquea el resto del día); con DLL es más barata |
| Consistencia | reto 40 % (o 50 % pagando); **fondeada sin consistencia** |
| Tamaño | reto 4 minis / 40 micros; fondeada 20 micros (< 1.000 $ de beneficio), 30 (< 2.000 $), 40 |
| Retiros | 5 días con ≥ 150 $; 50 % del beneficio hasta 2.000 $; mínimo 500 $; 90 %; tras 5 retiros pasa a Live |
| Horario | todo cerrado a las 16:45 ET (el ORB sale a las 15:30 ET) |
| Bots | **permitidos** ("Automated trading systems and trade copiers are permitted"); prohibidos HFT, microscalping y cobertura entre cuentas |
| Plataformas | NinjaTrader, Tradovate, TradingView (CQG) y otras (Rithmic); **no MT5** |
| España | no está en la lista de países restringidos |

El precio no aparece en la web de soporte; uso ~80 $ con cupón (115 $ sin cupón como prueba de sensibilidad).

## 2. El port a NinjaTrader y su validación

`ORB_MNQ_Lucid.cs` hace lo mismo que el v018, con el reloj de Nueva York (convierte desde la zona horaria de NinjaTrader):
rango 9:30-9:40, dirección de la vela, cuerpo ≥ 10 %, entrada a mercado, stop 15 % del ATR(14) diario de ayer (media simple
del TR como iATR de MT5, no la de NinjaTrader), filtro de volatilidad p90 de 252 días, trailing 3R/1R en el reto, stop a
entrada a +2R en la fondeada, salida 15:30 (14:00 los días de FOMC), festivos bloqueados y como mucho una operación al día.
Además vigila las reglas de Lucid: suelo del MLL, consistencia (deja de operar al superar el reto), topes de micros por
escalado y la pérdida diaria si se activa.

`orb_mnq_ref.py` es la réplica Python del .cs (velas con sello de cierre como NinjaTrader, orden de cálculo igual). Sobre los
mismos datos M1 que la serie v018 (Dukascopy 2018-21 y FTMO 2021-26):

| | Port (réplica) | Serie v018 |
|---|---|---|
| Operaciones 2018-01 a 2026-09 | 1.813 | 1.810 |
| Días comunes | 1.753 (96,9 % de la serie) | |
| Reto (trailing): corr / mismo signo / R media | 0,999 / 99,9 % / +0,117 | +0,115 |
| Fondeada (BE 2R): corr / mismo signo / R media | 0,999 / 99,8 % / +0,203 | +0,198 |

Los 57 días que solo están en la serie son 21 festivos que el EA bloquea, 5 por el filtro de volatilidad y 31 sin señal o sin
datos al abrir; los 60 que solo están en el port son días que la serie descartaba por su propio filtro. Nada sistemático.

Limitación: la réplica usa el CFD US100, no el futuro MNQ (no tengo velas de MNQ). El paso que falta es el backtest de
NinjaTrader con MNQ real (`comparar_nt.py` lo compara con la réplica).

## 3. Cuánto da Lucid con micros enteros (`lucid_sim.py`, 1 año, 10.000 trayectorias)

Stop real de cada día en puntos; micros = redondeo de riesgo / (stop × 2 $ + 2 $ de coste), sin pasar de +25 %.

| Riesgo | Media €/año | Mediana | Año < 0 | Caja p10 | Costes ×2 | Tipo 2018-21 | Cuota 115 $ |
|---|---|---|---|---|---|---|---|
| 300 $ | 2.640 | 1.690 | 22 % | −570 | 2.190 | 1.610 | 2.440 |
| **350 $** | **2.900** | **1.950** | **24 %** | **−640** | **2.490** | **1.700** | **2.670** |
| 400 $ | 2.940 | 2.080 | 26 % | −790 | 2.580 | 1.730 | 2.680 |
| 500 $ | 2.770 | 1.770 | 32 % | −1.070 | 2.200 | 1.840 | 2.450 |

- Elijo **350 $**: 400 $ da casi lo mismo con un 25 % más de caja en riesgo.
- Redondear a micros enteros apenas cuesta (con riesgo real medio 0,99-1,00 del objetivo). En 2026 el stop ronda 70 puntos
  (≈ 143 $ por micro), así que cada día son 2 o 3 micros.
- Probado y descartado: recortar el tamaño cerca del suelo o dar la cuenta por agotada baja la media 400-650 €. Con una cuota
  de 80 $ es mejor arriesgar el tamaño normal y recomprar. El EA lo trae apagado.
- Supuesto: tras 5 retiros la cuenta pasa a Live y aquí se da por terminada (Lucid no publica cómo sigue).

## 4. Segunda firma MT5: The5ers frente a FundingPips

| | The5ers High Stakes 10K | FundingPips 2-Step 10K |
|---|---|---|
| Precio | 78 $ (≈ 70 €), sin cupones grandes | 72 $ (≈ 58 $ con HELLO 20 %) |
| Fases | 10 % / 5 %, diaria 5 %, máx. 10 %, 3 días con ≥ 0,5 % | 8 % / 5 %, diaria 5 %, máx. 10 % |
| EA | cualquiera si tienes el código fuente y el stop es visible | EA propio con prueba de autoría |
| Apalancamiento índices | 1:25 → cabe el 2 % | 1:5 en Master → riesgo fondeado ~1 % |
| Noticias | no abrir órdenes de 2 min antes a 2 min después | Master: se anula el beneficio a ±5 min |
| Otros | copiar tus propias operaciones entre cuentas permitido; máx. 3 cuentas de 10K | prohíbe VPS; Master cierra a las 22:45 Madrid |
| **Media €/año (1 cuenta, 2022-26)** | **+2.840** (mediana +2.490, caja p10 −490) | +2.280 (caja −310) |
| Tipo 2018-21 | +1.880 | +1.560 |

Fuentes: the5ers.com (FAQ de EA 22/07/2026, apalancamiento 15/09/2026, reglas High Stakes 03/11/2026), propfirmmap (precios,
06/09/2026), memoria de FundingPips (web oficial 30/10/2026). Simulación con `dos-orb/diez_k.py` (modelo FTMO 2-Step).

**Elijo The5ers.** FundingPips arriesga menos caja, pero rinde ~550 € menos al año, su norma de noticias anula beneficios y
el apalancamiento obliga a bajar el riesgo. Los .set están en `black-friday-ea/`. Antes de arrancar hay que confirmar la hora
del servidor de The5ers (ver `black-friday-ea/LEEME.md`).

## Archivos

- `lucid-mnq/`: `ORB_MNQ_Lucid.cs`, `LEEME_NINJATRADER.md`, `orb_mnq_ref.py`, `comparar.py`, `comparar_nt.py`, `lucid_sim.py`,
  `lucid_sim_salida.txt`, `ref_combinada.csv`.
- `black-friday-ea/`: `ORB_US100_AGR_v018.mq5` (CSV con nº de cuenta), 6 .set, `hacer_sets.py`, `LEEME.md`.
- Copia en el PC: `Prop Firm Challenges\lucid_mnq\` y `Prop Firm Challenges\black_friday_ea\`.
