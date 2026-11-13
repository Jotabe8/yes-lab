# Preregistro · Oro largo en horas de Asia con coste Darwinex Zero (13-11-2026, antes de ver datos nuevos)

**Por qué se reabre:** en el registro está como clase B ("bruto ≈ coste"): ronda 2 (oct-2026) dio bruto +4,1 pb/noche
en ajuste (t 2,7) y +7,4 pb en prueba (t 5,0), pero con la horquilla de Dukascopy en la pausa diaria el coste era
~7 pb. En Darwinex Zero el oro cuesta mucho menos:
- **Futuro GC (cuenta de futuros):** 1 tick (10 $) + 3 $ × 2 órdenes ≈ 16 $ sobre 200-400 k$ de nominal ≈ **0,4-0,8 pb ida y vuelta**.
- **CFD XAUUSD (cuenta CFD):** 0,46 pt + 0,0025 % × 2 ≈ **1,6-2,8 pb**; sin swap si se entra después del corte diario y se sale antes del siguiente.

**Mecanismo (T1):** compra física asiática (China, India) en sus horas y venta/cobertura en horas de Londres-NY.
Riesgo principal: que sea solo la subida del oro (beta). Por eso el contraste principal es **noche contra día**, no noche contra cero.

**Datos:** Dukascopy XAUUSD H1 bid y ask 2012-01 → 2026-11, **precio medio** (evita el artefacto de la horquilla en la pausa).

**Regla:** largo de **19:00 a 03:00 hora de Nueva York** (8 h; entra 1 h después de la reapertura de las 18:00,
sale a las 8:00 de Londres), noches de domingo a jueves. Coste por noche 1 pb (GC) y 2 pb (CFD).

**Principal (1 prueba):** diferencia diaria pareada `D = r_noche − (8/15) × r_resto`, donde `r_resto` es la
rentabilidad de las 15 h restantes de sesión (03:00 → 18:00 NY). Neutraliza la deriva: si el oro sube igual a todas
horas, D ≈ 0. **Pasa si** t(D) ≥ 2,4 en 2012-2026, ambas mitades (2012-18 y 2019-26) > 0, y la noche neta con
coste GC ×2 > 0.

**Informativas (cuentan para el total, 5 pruebas):** noche neta GC y CFD; placebo de 8 h en las otras ventanas
(03-11, 11-19 NY) y en 50 ventanas de 8 h con hora de inicio al azar; año a año; plata (XAGUSD) como réplica del
mecanismo (sin poder de rescate).

**Si pasa:** EA para la cuenta de futuros (GC) o CFD; correlación con el ORB US100 y proyección DZ.
**Si falla:** se queda en el registro con su clase, sin rescates.

---

## Resultado de la prueba principal (13-11-2026): NO PASA

Salida completa en `oro_asia_salida.txt`. D = +2,1 pb t 2,03 (< 2,4); 2012-18 +3,0 pb t 2,2 pero 2019-26 +1,3 pb t 0,8;
noche neta con GC ×2 −0,2 pb. La ventana 19:00-03:00 es la 10ª de 24 en el placebo de hora. Plata: D ≈ 0.
Clase **A** (sin ventaja con coste bajo). Sin rescates.

## Preregistro 2 · Oro en la apertura asiática, 19:00 → 22:00 NY, confirmado en datos sin tocar 2003-2011

**Origen (hallado mirando los datos, por eso NO cuenta 2012-26 como prueba):** el desglose hora a hora de 2012-26
muestra que la subida del oro se concentra en 17:00-21:00 NY, con las horas 19, 20 y 21 positivas en las dos mitades
(19:00 NY = 8:00-9:00 de Tokio: apertura de Asia). Las horas 17 y 18 incluyen la pausa y la reapertura (posible
artefacto de cotización), así que se excluyen. En 2012-26: 19→22 ≈ +1,6 pb/día, t ≈ 4, con el oro bajando de media en el resto del día.

**Prueba única:** largo XAUUSD **19:00 → 22:00 hora de Nueva York**, todas las sesiones de domingo a jueves,
precio medio Dukascopy H1, **2003-05 → 2011-12** (datos que no se han mirado en este proyecto).
**Pasa si:** media bruta ≥ +1,0 pb con t ≥ 2,4; ambas mitades (2003-07, 2008-11) > 0; la ventana es mejor que
la mediana de las 24 ventanas de 3 h en esos años (placebo de hora); y neta con coste GC ×2 (1 pb) > 0.
**Informativo:** plata, año a año. Si pasa: EA para la cuenta de futuros (GC) y proyección DZ. Si falla: clase A.
