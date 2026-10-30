# Preregistro: víspera de festivo en índices (2026-10-30)

Escrito antes de mirar resultados. Efecto publicado: Ariel (1990), Kim y Park (1994): el día anterior
a un festivo bursátil rinde varias veces un día normal (≈ 0,2-0,3 % frente a ≈ 0,03 %). Causa propuesta:
cierre de cortos y optimismo antes del puente; nadie quiere quedarse corto con el mercado cerrado.

- **Regla:** en cada índice, el último día de negociación antes de un festivo entre semana de ese mismo
  mercado (detectado por su propio calendario: el siguiente día de negociación no es el siguiente día
  laborable) se compra. Variante A: apertura → cierre del mismo día (intradía, sin swap).
  Variante B: cierre del día anterior → cierre de la víspera (una noche de swap).
- **Salidas:** sin stop, o con stop de 1 ATR(20) diario desde la entrada comprobado con el mínimo del día
  (solo en la variante A, donde el mínimo es posterior a la entrada). 1 R = 1 ATR(20). n_pruebas = 3.
- **Mercados:** 13 índices de `datos_tendencia/` (US500, US100, US30, US2000, GER40, FRA40, EU50, SPA35,
  NLD25, UK100, JP225, HK50, AUS200).
- **Periodos:** ajuste 2000-2022, prueba 2023-2026 abierta una vez.
- **Costes:** spread 0,02 % (EE. UU.) o 0,04 % (resto) ida y vuelta; B paga además una noche a tipo + 6,5 %.
- **Umbral:** P1 si bruto ≥ 3× coste, por encima del p95 del placebo (días normales al azar, mismo nº por
  mercado y mismas salidas, 500 réplicas) y positivo en ≥ 2/3 de los índices. Luego P2-P4 del método.
