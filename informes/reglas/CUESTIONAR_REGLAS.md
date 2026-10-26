# Revisión de las reglas del proyecto (2026-10-26)

Jorge pidió cuestionar todos los principios que me había dado. Este documento revisa cada regla y prueba las dos que podían estar limitando.

## Regla por regla

| Regla | ¿Limita? | Motivo |
|---|---|---|
| Fuera de muestra, placebos, walk-forward | No | Solo descartan falsos positivos. Antes de costes, los mejores NNFX ganan +0,01 a +0,03 R por operación, así que quitar estas pruebas no cambia el resultado. |
| Costes al doble (2,2 pips × 2) | Poco | 2,2 pips es más de lo que cobra FTMO de verdad (≈0,8 pips con comisión en las mayores). En D1 la diferencia es de unos 0,01 R por operación. |
| Excluir la Dirty Dozen | No | RSI(2), Bollinger, Donchian/EMA y los cruces ya fallaron en pruebas anteriores. |
| Python antes que MQL5 | No | Es solo el orden de trabajo. |
| "Hace falta edge" | **Podía limitar** | La prueba de Pons mostró que, con coste bajo en R, una moneda al aire da EV + por cuota. Se prueba abajo. |
| "Lo que no vale solo se descarta" | **Podía limitar** | Impide sumar ventajas débiles que no se parecen entre sí. Se prueba abajo. |
| Buscar a lo bruto (impuesta por mí) | Sí | Con 80.000 combinaciones, el azar solo ya da t ≈ 4. Es mejor probar pocas hipótesis con buena base. |

## Prueba: EV por cuota sin edge, y en combinación con el ORB
- **Serie NNFX:** el sistema NNFX D1 que eligió el walk-forward año a año (2017-2026, biblioteca pandas-ta, 12 mercados). Son 998 operaciones, con +0,019 R neto (coste 1x) y +0,001 R al doble.
- **Simulador:** `cartera/equilibrio.py` de Jorge, con las reglas oficiales de FTMO, 632 € de presupuesto en cuotas, 1 año y bloques de 20 días.
- **Cómo se juntan los dos EAs:** el R de cada día se suma, con el mismo riesgo para los dos.

| Serie (2018-2026) | Mejor cuenta | Neto medio/año | P(neto > 0) |
|---|---|---|---|
| ORB US100 solo | 2-Step 200K, 1 % | +7.507 € | 35 % |
| NNFX solo, coste 1x | 1-Step 100K, 1,5 % | −66 € | 9 % |
| NNFX solo, coste 2x (edge ≈ 0) | — | −79 € (no compensa ni una cuota) | 0 % |
| ORB + NNFX, coste 1x | 2-Step 200K, 1 % | +8.159 € | 35 % |
| ORB + NNFX, coste 2x | 2-Step 200K, 1 % | +7.363 € | 34 % |

## Conclusiones
1. **La estructura de la prop no rescata un sistema sin edge.** La moneda de Pons daba EV + porque operaba mucho, con coste casi nulo y ganancias y pérdidas simétricas. Un NNFX D1 hace unas 100 operaciones al año, tiene un perfil de R peor y cae en el drawdown diario y en el trailing antes de llegar al objetivo. Así que la regla "hace falta edge" era correcta.
2. **Sumar el NNFX al ORB añade +650 €/año con coste 1x, pero resta 140 €/año al doble.** Es una mejora que depende del coste y queda dentro del ruido del Monte Carlo. No compensa mantener un segundo EA.
3. **Las reglas no eran el freno.** Lo que limita es que en forex y oro D1 no hay ventaja que encontrar con indicadores, carry, COT ni estacionalidad. El edge real del proyecto sigue siendo el ORB.
