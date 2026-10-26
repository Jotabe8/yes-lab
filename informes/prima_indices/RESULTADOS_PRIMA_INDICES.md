# Cesta larga de índices con volatilidad objetivo: dónde está la ventaja

Fecha: 2026-10-26. Scripts: `prima.py` (estrategia), `ev_prima.py` (EV por cuota) y `control.py` (controles sin edge).

## Estrategia (reglas fijadas antes)
- **Qué compra:** se va largo en S&P 500, Nasdaq 100, Dow, DAX, FTSE y Nikkei cuando el cierre está por encima de su media de 200 sesiones (Faber 2007).
- **Tamaño:** cada mercado busca una volatilidad del 10 % anual, con palanca máxima de 2x. La cartera pesa lo mismo en riesgo por mercado.
- **Costes:**
  - Financiación diaria: tipo a 3 meses + 2,5 % (caso malo: + 3,5 %).
  - Spread: 0,02 % por cambio de tamaño.
  - Dividendos: con y sin ellos, porque no sé si FTMO ajusta dividendos en los CFD.
- **Datos:** índices diarios de Yahoo desde 1985 y tipos de FRED, descargados con el workflow `descargar-macro.yml`.

## La estrategia por sí misma: casi sin edge

| | Sharpe 2008-2026 | maxDD |
|---|---|---|
| Con filtro de 200 sesiones, financiación + 2,5 % | 0,28 | −17 % |
| Ídem, financiación + 3,5 % | 0,19 | −18 % |
| Sin filtro, + 2,5 % | 0,36 | −24 % |
| 2018-2026, sin dividendos, + 2,5 % | 0,09 | −17 % |
| 2018-2026, con dividendos, + 2,5 % | 0,24 | −16 % |

La financiación del CFD se come casi toda la prima de riesgo. Solo el Nasdaq 100 destaca (Sharpe 0,57), y eso es mirar atrás.

## EV por cuota (simulador `equilibrio.py`, reglas FTMO, 632 € de presupuesto)

| Serie (2018-2026, bloques de 20 días) | Horizonte | Mejor cuenta | Neto medio |
|---|---|---|---|
| ORB US100 solo | 1 año | 2-Step 200K | +7.309 € |
| ORB US100 solo | 3 años | 1-Step 200K | +11.797 € |
| Cesta de índices sola, sin dividendos | 3 años | 2-Step 200K | +4.492 € |
| Cesta de índices sola, con dividendos | 3 años | 2-Step 200K | +7.423 € |
| ORB + cesta en la misma cuenta | 3 años | 2-Step 200K | +12.096 € (≈ ORB solo) |

## Control: ¿es edge o es la estructura de la prop?

| Serie con la misma volatilidad | 3 años, mejor cuenta |
|---|---|
| Cesta real | +4.492 € |
| Cesta con media puesta a 0 | **+3.553 €** |
| Cesta con media de −2 %/año | +1.402 € |
| Ruido normal i.i.d., media 0 | +1.579 € |

**Conclusión:** casi todo el EV sale de la estructura de pago de FTMO, no de la estrategia. Si pierdes, pierdes la cuota; si ganas, cobras retiros sobre 200K. Con coste por operación casi nulo, la exposición es continua y diversificada, el drawdown es suave y hay pocos días de pérdida grande. Así, hasta una serie sin edge da EV positivo. El NNFX no lo conseguía porque paga spread en cada operación y tiene pérdidas discretas de 1 R que caen en el límite diario.

Las autocorrelaciones reales ayudan (+3.553 € frente a +1.579 € con ruido i.i.d.). El objetivo de volatilidad y el filtro de tendencia hacen la curva más suave que un ruido puro.

## Riesgos antes de convertirlo en EA
1. **Fin de semana:** en las cuentas fondeadas Standard está prohibido mantener posiciones durante pausas de más de 2 horas. Hace falta la cuenta **Swing**, que tiene menos apalancamiento. En el reto y la verificación no hay restricción.
2. **Prácticas prohibidas:** FTMO pone las "one-sided bets", la sobreexposición y la "exposición acumulada en símbolos correlacionados" como ejemplos de trading prohibido. Una cesta solo larga de índices encaja con esa descripción, y FTMO podría denegar retiros. Este es el riesgo principal y no se puede medir en Python.
3. **Riesgo alto, cerca del borde:** el EV máximo aparece con el riesgo más alto probado (2x, vol ≈ 14 %). Si se usa, debe ser con una exposición moderada (vol 7 %), que se parezca a una gestión normal.
4. **El simulador es un modelo:** el EV depende de cómo modela FTMO (retiros cada 10 días, devolución de la cuota). Las cuotas y las reglas pueden cambiar.
5. **Regla de gap:** no se puede abrir posiciones en las 2 horas antes de una pausa de 2 horas o más. Hay que reequilibrar a media sesión y nunca el viernes por la tarde.

## Añadido: largo/corto y riesgo moderado
- **Versión largo/corto** (corto bajo la media de 200): el Sharpe 2008-2026 baja a 0,01-0,11, porque el corto paga dividendos, cobra poco por la financiación y va contra la deriva. A 3 años da +1.578 / +2.791 € en 2-Step 200K con riesgo máximo, y ≈ 0 con riesgo moderado. **Peor que solo largo.**
- **Solo largo con riesgo moderado** (volatilidad ≈ 7 %), 3 años, 1-Step 200K: **+3.069 € sin dividendos y +4.671 € con dividendos**. En 2-Step 200K: +1.011 / +2.129 €. En 2-Step el mejor riesgo es ≈ 10-14 % de volatilidad (+3.955 a +7.423 €).
- Con un riesgo moderado y normal ya sale EV positivo, sin tener que llegar a la sobreexposición.
