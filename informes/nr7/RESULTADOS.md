# Ruptura intradía tras día estrecho (NR7): descartada en P1 (2026-10-30)

**Veredicto.** Con índices de contado de Yahoo parecía muy buena (+0,08 R neto, t 9,6 en 18 mercados).
Era un **artefacto de los datos**: con futuros, que son precios que se pueden negociar, la misma regla da
≈ 0 bruto y pierde en neto en los cuatro índices de EE. UU. n_pruebas = 3; la prueba 2023-26 no se abrió.

## Primera lectura (contado, ajuste 2000-2022)

| Variante | Ops/año | Bruto R | Coste R | Neto R (t) | Mercados + |
| --- | --- | --- | --- | --- | --- |
| NR7 | 631 | +0,163 | 0,081 | +0,082 (9,6) | 13/18 |
| NR4 | 1.055 | +0,148 | 0,073 | +0,075 (12,0) | 13/18 |
| Día interior | 467 | +0,166 | 0,070 | +0,097 (10,4) | 16/18 |

Señales de alarma (`diag_salida.txt`): ganaba igual en días normales que tras un NR7; lo mejor eran
US2000 (+0,33 R), AUS200 (+0,27) y US30/US500 de contado, y lo peor el US100 (−0,02), el índice
más líquido y el único que operamos de verdad. Es la huella de los precios rancios: el índice de
contado se calcula con la última operación de cada acción, y las acciones pequeñas tardan en cotizar.
Eso crea continuidad dentro del día que no se puede negociar.

## Control con futuros (2002-2022; RTY desde 2017)

| Serie | NR7 neto R (t) | Todos los días neto R (t) |
| --- | --- | --- |
| US500 contado | +0,180 (5,3) | +0,081 (7,5) |
| **ES (futuro)** | **−0,074 (−2,4)** | −0,062 (−6,3) |
| US100 contado | −0,025 | −0,024 |
| **NQ (futuro)** | **−0,058** | −0,052 |
| US30 contado | +0,154 (4,3) | +0,069 |
| **YM (futuro)** | **−0,051** | −0,043 |
| US2000 contado | +0,283 (4,1) | +0,141 |
| **RTY (futuro)** | **−0,049** | −0,041 |

Los CFD de FTMO siguen al futuro, no al contado. Bruto con futuros: −0,02 a +0,01 R. **Descartada.**

**Lección para el método:** no probar reglas intradía (máximos, mínimos o apertura del día) con
índices de contado de Yahoo; usar futuros o los M1 de Dukascopy o FTMO. Las reglas que solo usan el
cierre son menos sensibles, pero conviene revisarlas igual.
