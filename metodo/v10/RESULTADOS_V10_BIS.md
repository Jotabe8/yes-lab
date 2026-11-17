# v10-bis: resultado (15-11-2026)

Datos: operaciones SIP de QQQ de Alpaca, 9:30:00-9:39:59 ET, 2.230 días (2018-01-02 → 2026-11-13), mediana de 10.361
operaciones y 1,9 M acciones por ventana. Volumen con signo por la regla del tick, sin la subasta de apertura ni lotes
impares. Cruzado con las 1.763 operaciones del ORB v018 (serie_v018_be.csv). Salida: `analizar_alpaca_salida.txt`.

| Prueba | Resultado | Listón | Veredicto |
|---|---|---|---|
| H2a: el ORB rinde más si el flujo va con la vela | Acuerdo 1.149 ops +0,223 R; desacuerdo 614 ops +0,191 R; dif +0,032, t 0,29 | dif ≥ 0,15 y t ≥ 2,4 | **No pasa** |
| Mitades | 2018-21 +0,190; 2022-26 −0,085 | las dos ≥ +0,05 | No pasa |
| Grupo que quitaría el filtro | +0,191 R | ≤ +0,02 | No pasa: quitarlo baja el R total |
| Placebo (2.000 barajados) | p95 +0,185 | real > p95 | No pasa |
| Réplica 9:30-9:35 | t −0,22 | t ≥ 1,5 | No pasa |
| H2b: más flujo, más R (días de acuerdo) | tercio alto +0,340, bajo +0,188, dif +0,151, t 0,92 | (mismo listón) | No pasa |

**Descartada (clase A: sin efecto).** El volumen con signo de la apertura no dice nada que la vela del rango no diga ya:
el ORB gana lo mismo cuando el flujo va a favor que en contra, y en 2022-26 incluso algo más en contra. Con 1.763
operaciones la prueba tenía potencia para ver una diferencia de ~0,25 R; la real es 0,03.

Con esto la v10 queda cerrada: sitio barato agotado (gotobi cerrado por la horquilla real), desequilibrios de subasta sin
fuente sin Databento, y flujo de la apertura sin efecto. El ORB US100 sigue siendo el único sistema.
