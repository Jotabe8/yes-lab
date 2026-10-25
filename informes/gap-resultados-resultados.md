# Resultados: continuación del gap de resultados en acciones de EE. UU.

Fecha: 2026-10-25. Reglas fijadas antes de ver los datos en
[gap-resultados-preregistro.md](gap-resultados-preregistro.md). Salida completa en
[gap-resultados-salida.txt](gap-resultados-salida.txt) (`python -m lab.gap_resultados`).
Nada de esto es una recomendación de inversión.

## Veredicto: descartada

Falla el criterio principal. En el universo amplio (71 acciones) el efecto fuera de muestra es
+0,028 R por operación con t = 0,74, y al doble de coste es negativo.

| Fuera de muestra 2018-2026 | Operaciones | R/op bruto | R/op neto | t | Neto ×2 coste |
| --- | --- | --- | --- | --- | --- |
| Amplio (71 acciones) | 638 | +0,078 | +0,028 | 0,74 | −0,022 |
| Lista FTMO (23 acciones) | 249 | +0,186 | +0,138 | 2,26 | +0,090 |

Criterios: 1 (amplio, t ≥ 2 y positivo al doble) **falla**; 2 (FTMO positivo) pasa; 3 (años
positivos) pasa, 6 de 9 en el amplio y 7 de 9 en FTMO; 4 (correlación con el QQQ −0,19 y
−0,16) pasa. El 5 (Monte Carlo 2-Step con el ORB) no se llega a hacer.

## Lo que hay que saber

- El efecto existe antes de costes en el universo amplio (+0,078 R, t = 2,06), pero el coste del
  CFD (unos 0,24 % por operación con el swap de 7 noches) se lleva casi todo. Es otra vez la
  lección del proyecto: el movimiento medio a favor es de 0,42 %, no del 1-3 % que se esperaba.
- La lista FTMO sale bien porque son sobre todo tecnológicas volátiles (TSLA, NVDA, NFLX, META,
  AMD, ZM). Eso es selección a posteriori más sesgo de supervivencia: son las acciones que hoy
  son populares. El resto de grandes compañías (48) no aporta nada o resta. Probar ahora "solo
  acciones volátiles" sería una variante de rescate, y por la regla del proyecto no se hace.
- La sensibilidad no muestra una zona robusta: con volumen ×2 pierde, y solo mejora en
  extremos con pocas operaciones (volumen ×5, 172 operaciones, t = 1,67).
- En la lista FTMO hay solo unos 28 eventos al año: aunque funcionara, aportaría poca
  frecuencia a una cuenta de prop.

## Límites

Datos diarios de Yahoo (sin spread real del CFD al cierre); lista de acciones FTMO no
confirmada en el terminal; universo de supervivientes.
