# ORB en otros índices: prerregistro

Escrito el 2026-10-26, antes de ver ningún resultado. Prueba simulada, sin dinero real.

## Pregunta

¿La ventaja del ORB_US100 v0.16 (+0.15 R fuera de muestra en US100, 2021-2026) es una propiedad
de la apertura de los índices o una casualidad de US100 en esos cinco años?

## Qué se prueba

- **La misma regla, sin reajustar nada**: rango de 10 minutos desde la apertura cash, dirección de
  la vela (cuerpo ≥ 10% del rango), stop al 15% del ATR(14) diario, sin objetivo, una operación al
  día, riesgo 0.5%. Solo se traduce el reloj de cada bolsa (`lab/orb_indices.py`).
- **Mercados**: US500 y US30 (apertura 16:30 del servidor, cierre 22:30, festivos NYSE) y GER40
  (apertura de Xetra, 10:00 del servidor u 11:00 en las semanas de desfase de horario, cierre a las
  18:00, festivos de Xetra).
- **Más historia**: US100 antes del 14-09-2021 con velas M1 de Dukascopy. Es historia que no se usó
  para elegir la configuración.
- **Costes**: spread de la vela de entrada más deslizamiento fijo proporcional al de US100; todo se
  repite con costes al doble.
- **Walk-forward**: 3 años de ajuste y 1 de prueba con la rejilla del PR #2 (rango 5/10/15/30 min,
  stop 10/15/20/30% del ATR). Se mira sobre todo la configuración fija.

## Criterios (decididos ahora)

| | Criterio | Se cumple si |
| --- | --- | --- |
| A | Historia nueva de US100 | R medio > 0 con costes al doble antes de 14-09-2021 |
| B | Generaliza a otros índices | R medio > 0 con costes al doble en al menos 2 de US500, US30 y GER40 |
| C | No depende de una época | ≥ 60% de los años-mercado con R medio > 0 (costes normales) |
| D | Walk-forward | Configuración fija encadenada positiva con costes al doble en al menos 3 de los 4 |

**Veredicto**: *robusta* si se cumplen A, B, C y D; *frágil* si se cumplen A y solo uno de B o D;
*casualidad de US100* si falla A y falla B. Cualquier otra combinación es *mixta* y se explica.

Antes de juntar dos fuentes se comparan en el periodo común (mismo lado y correlación de R por
operación). Si coinciden menos del 80% de los lados, la fuente antigua se trata con cautela.
