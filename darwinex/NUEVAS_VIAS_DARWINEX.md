# Otras formas de encontrar sistemas para Darwinex (13-11-2026)

## Resumen

1. **En Darwinex no hay ventaja "de estructura".** En FTMO, una serie sin ventaja podía dar valor esperado positivo
   por cuota. En Darwinex no: un DARWIN con la misma volatilidad que los dos ORB pero media 0 pierde unos 440 €/año
   y acaba en negativo el 93 % de las veces (`control_cero.py`). **Solo paga la ventaja real.** Darwinex reescala el
   riesgo, así que no se puede comprar con volatilidad.
2. **Lo nuevo que permite Darwinex son los bonos (futuros ZT, ZF, ZN y ZB), las materias primas en contrato estándar y
   mantener posiciones varios días sin swap.** He probado las dos ideas con mecanismo y bonos que mejor salían en el triaje:
   - **Ciclo de subastas del Tesoro:** el efecto es **real y sigue vivo fuera de la muestra del artículo** (2009-2026:
     +10 pb por ciclo, t 3,9, pasa todo el preregistro sobre los rendimientos de FRED). **Pero en los futuros, que es
     lo que se puede operar, casi desaparece** (+3 pb, neto ≈ 0). Vive en el bono recién emitido, no en el
     entregable del futuro. Clase B: no operable en Darwinex.
   - **Rebalanceo de pensiones a fin de mes (S&P frente a bono a 10 años):** t neto 2,15 < 2,4, y negativo fuera de
     la muestra publicada (2023-26: −13 pb). Descartado.
3. **Lección para el método:** probar siempre en el **instrumento que se va a operar** desde el principio. La serie
   "limpia" (FRED, índices de contado) puede tener un efecto que el contrato no tiene. Es la misma familia de error
   que los precios rancios de Yahoo.

## 1. Qué permite Darwinex que FTMO no

| Palanca | Qué abre | Qué se ha comprobado |
|---|---|---|
| Futuros estándar con 1 M$ y sin pérdida máxima | Contratos baratos en R (BTC, ETH, NQ, ES, FDAX, CL, GC) | ORB cripto operable (hilo anterior) |
| Bonos (ZT/ZF/ZN/ZB, Bund en Eurex) | Ciclos de oferta del Tesoro, flujos de fin de mes, FOMC | Subastas: no operable en futuros; pensiones: no |
| Multi-día sin swap | Primas de riesgo, tendencia, carry | Momentum y cesta: beta, no ventaja (hilo anterior) |
| Sin reto ni límite diario | Estrategias con colas o DD largos | No cambia el listón: el rating castiga el DD y premia 6 meses |
| Rating por retorno/DD a VaR fijo | Mezclar estrategias descorrelacionadas | Los dos ORB: Sharpe 1,33 → 1,72 |
| Estructura de pago | ¿Gana una serie sin ventaja? | **No**: −440 €/año de media |

## 2. Triaje T0 (sin datos) de ideas que solo caben en Darwinex

| Idea | Ops/año | Problema | Veredicto |
|---|---|---|---|
| Ciclo de subastas del Tesoro (Lou-Yan-Zhang 2013) | ~35 ciclos | Potencia justa (Sharpe ~0,5-0,7) | **Probada** |
| Rebalanceo de pensiones a fin de mes (Harvey et al. 2025) | 12 | Potencia justa; artículo reciente | **Probada** |
| Deriva pre-FOMC en bonos | 8 | Potencia: > 50 años | fuera |
| Subida de los bonos a fin de mes por extensión de índices | 12 | Efecto 3-5 pb, potencia | fuera |
| Adelantarse al roll del GSCI (diferenciales de materias primas) | 12 | Hacen falta curvas de futuros (no hay datos gratis); efecto apagado tras 2010 | fuera |
| Carry de materias primas (curva) | 12 | Sharpe publicado 0,5 → 0,25: siglos de historia | fuera |
| ORB del ZN o del Bund en su apertura | 250 | Tick de 1,5 pb frente a un stop de 0,15 ATR: margen < 2 | fuera |
| ORB del crudo a las 9:00 NY | 250 | Ya cubierto: el ORB en USOIL a las 8:30 y 9:30 no superó al placebo | fuera |
| Tendencia, momentum o cestas multi-día | — | Ya probado hoy: beta | fuera |

## 3. Resultados de las dos pruebas (preregistro `PREREGISTRO_BONOS.md`, commit 10ee2cb)

### 3.1 Ciclo de subastas (pb por ciclo a riesgo del 5 años; coste 3 pb)

| | n | Bruto | Neto (t) | 2.ª mitad | Costes ×2 |
|---|---|---|---|---|---|
| **FRED 2009-2026 (principal)** | 624 | +10,3 | **+7,3 (2,79)** | +4,3 | +4,3 |
| Placebo dos semanas después | 622 | +0,6 | −2,4 | −6,0 | |
| FRED 1990-2008 (réplica) | 389 | +18,5 | +15,5 (3,28) | | |
| **Futuros 2009-2026 sin días de roll (informativo)** | 914 | **+3,2 (t 1,5)** | **+0,2 (0,08)** | +0,9 | −2,8 |
| FRED en ese mismo subconjunto | 930 | +10,4 | +7,4 (2,95) | | |

- Por plazo (FRED): el más fuerte es el de 5 años (+13 pb neto, t 2,9, estable en las dos mitades); el de 2 años se apaga
  después de 2017. Por año: 2023, 2024 y 2025 negativos (−4 pb cada uno).
- Con los futuros: 5 años +6 pb bruto (t 1,3), 10 años +6 pb (t 1,5), 2 y 30 años ≈ 0. El futuro sigue al bono más barato de
  entregar, no al recién subastado, que es el que se abarata.
- **Registro: clase B (lugar).** Se reabre solo con acceso al bono del Tesoro recién emitido (contado o CFD sobre él) con
  coste ≤ 3 pb por ciclo. Darwinex no lo ofrece; los ETF de bonos tampoco sirven (mezclan emisiones).

### 3.2 Rebalanceo de pensiones (pb por operación; coste 3 pb)

| | n | Bruto | Neto (t) | 2.ª mitad |
|---|---|---|---|---|
| 1999-2026 (principal) | 334 | +21,2 | +18,2 (2,15) | +6,3 |
| Placebo a mitad de mes | 334 | −7,7 | −10,7 | |
| 2023-04 → 2026-10 (fuera de la muestra del artículo) | 43 | −10,2 | −13,2 | |

Supera al placebo y el signo coincide con el artículo, pero no llega a t 2,4 y falla fuera de muestra. **Clase D, descartada.**

## 4. Vías para generar ideas, ordenadas por lo que hemos aprendido

1. **Lugar primero con el catálogo de Darwinex.** Cuando Darwinex dé la lista de los 60 futuros, cruzarla con las clases B
   del registro. Es lo que ha funcionado hoy con el ORB cripto. Candidatas: JP225 (NIY/NKD), si el coste en la apertura de
   Tokio es ≤ 0,005 %.
2. **Flujos forzados con calendario conocido, probados en el contrato desde el principio.** El siguiente candidato natural es
   el **ciclo de subastas dentro del día en los futuros** (presión hasta las 13:00 NY del día de subasta y rebote después).
   Hay unas 150 subastas al año, así que la potencia es mucho mayor. Hace falta M1 del ZN/ZF (Dukascopy tiene CFD de
   bonos; se bajaría con GitHub Actions).
3. **Aprender de los DARWINs que sobreviven.** Darwinex publica las estadísticas de los DARWINs con más años y asignaciones
   (activos, duración de las operaciones, horarios). No da reglas, pero dice en qué mercados y plazos hay gente cobrando
   de forma estable en esta plataforma. Es una fuente de hipótesis, no de pruebas.
4. **Diversificar por mecanismo, no por mercado.** Cada estrategia nueva tiene que pasar sola, pero lo que más sube el
   rating es una segunda o tercera estrategia con correlación ≈ 0 (como el ORB cripto).

Código: `bonos_dz.py`, `bonos_futuros.py`, `control_cero.py`. Datos: `datos_bonos/` (FRED, Yahoo y fiscaldata, bajados con
`datos-bonos-dz.yml`).

## Ronda 13-11 (tarde): oro en horas de Asia con coste de futuros GC

- **Oro largo 19:00-03:00 NY** (reabierta de clase B porque el GC cuesta 0,4-0,8 pb y no 7 pb): con precio medio
  2012-26 la noche gana +2,1 pb más que su parte de la deriva, t 2,0 (< 2,4); 2019-26 t 0,8; con coste ×2 pierde;
  queda 10ª de 24 ventanas de 8 h. **No pasa.**
- **Oro 19:00-22:00 NY** (la mejor franja vista en 2012-26, t ≈ 4) probada en datos sin tocar 2003-2011:
  +1,3 pb t 1,87, 10ª de 24 ventanas de 3 h, neta 1 pb ≈ 0. **No pasa:** lo de 2012-26 era deriva del oro repartida al azar entre horas.
- Lección: con 24 franjas horarias, la mejor de una muestra siempre parece fuerte; el control de datos anteriores
  (2003-11) es barato y debe ir siempre antes de escribir un EA.
