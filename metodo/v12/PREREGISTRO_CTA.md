# Preregistro v12: flujo forzado de los CTA (escrito el 15-11-2026 antes de mirar resultados)

## Por qué es una vía nueva
Los seguidores de tendencia (CTA, ~300-400 mil M$) calculan su posición con reglas públicas sobre el cierre.
Cuando su señal agregada cambia, tienen que comprar o vender al día siguiente: un pagador obligado con
horario conocido. Ya se probó seguir la tendencia (Donchian, NNFX: el swap la mata); nunca se probó el
**impacto de su ejecución en las horas siguientes al cambio**, que cabe dentro del día y no paga swap.
Datos: velas diarias (corte 17:00 NY) y M1 07:00-17:00 NY ya en metodo/v9/datos/ (Dukascopy, precio medio).
No requiere cuentas ni registros.

## Regla (fija)
- Señal CTA replicada: S_t = media de signo(C_t − C_{t−L}) para L ∈ {21, 63, 126, 252} sesiones.
- Flujo F_t = S_t − S_{t−1}. Día de evento: F_t ≠ 0. Dirección d = signo(F_t).
- Se opera la siguiente sesión NY tras el cierre de 17:00 del día t.
- Ventanas (2 variantes, no más):
  - W1: índices 09:30 → 15:59 (cierre); FX/oro 08:00 → 16:59.
  - W2: índices 15:00 → 15:59 (la hora en que ejecutan muchos CTA); FX/oro 16:00 → 16:59 (fix Londres excluido).
- Rendimiento en pb del precio medio; coste ida y vuelta: índices 0,8 pb, FX 0,8 pb, oro 1,2 pb.

## Mercados
- Principal: cartera US500 + US100 (media de los dos por día de evento, si ambos tienen evento).
  Si solo uno tiene evento ese día, cuenta solo ese.
- Réplica no mirada: EURUSD, GBPUSD, USDJPY, XAUUSD (cartera igual).

## Listones (todos, para W1 o W2)
1. t neto de la cartera principal ≥ 2,4 sobre 2011-2026.
2. Segunda mitad (2019-2026) neto > 0.
3. Con coste ×2 neto > 0.
4. Placebo 1 (dirección al azar en los mismos días, 2.000 sorteos): media > p95.
5. Placebo 2 (clon de momentum: d = signo del rendimiento del día t, mismos días): estrategia − clon > 0 con t ≥ 1,5.
6. Réplica FX/oro: mismo signo, t ≥ 1,5.
7. Al menos 40 eventos/año por mercado o se declara sin potencia.

## Potencia (T0)
σ de W1 en índices ≈ 100 pb y de W2 ≈ 30 pb. Con ~25 eventos/año/mercado y 15 años (~375 días de cartera)
el mínimo detectable a t 2,4 es ≈ 13 pb en W1 y ≈ 4 pb en W2. Un efecto menor queda como clase C (sin potencia).

## Si falla
Clase A/B/C según el registro de v3; se cierra la familia "flujo de seguidores de tendencia". No hay variantes extra.
