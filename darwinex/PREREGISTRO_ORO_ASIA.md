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
