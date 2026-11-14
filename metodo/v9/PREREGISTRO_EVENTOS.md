# Preregistro v9-A: ruptura en el instante del dato programado (NFP, IPC, FOMC)

Escrito el 14-11-2026 antes de bajar los datos (commit anterior al del workflow `v9-eventos.yml`).

## Mecanismo
El ORB US100 gana porque la apertura concentra información nueva y la primera vela marca la dirección
(Zarattini-Aziz). La misma lógica debería valer en el **instante en que se publica un dato programado**:
empleo (NFP, 8:30 NY), IPC (8:30 NY) y comunicado del FOMC (14:00 NY). La información es el **calendario
oficial** (BLS y Reserva Federal), no el precio. Familia nueva: "noticias US100" probó ruptura/desvanecer
en todos los días con noticias, la minería de 25.422 reglas miró las 8:30 de todos los días, y el ORB en
aperturas ajenas miró horas sin dato. Aquí solo los tres datos de más impacto, en 6 mercados a la vez.

## Datos
- Fechas: `eventos.csv` (BLS empsit y cpi archivados, calendario FOMC de la Fed; FOMC desde 2013, cuando
  todos los comunicados pasan a las 14:00). 190 NFP, 190 IPC, 110 FOMC.
- Precios: M1 Dukascopy bid/ask 2011-01 → 2026-11, precio medio, horquilla real minuto a minuto.
  XAUUSD, EURUSD, GBPUSD, USDJPY, US100, US500 (índices desde 2011-09).

## Regla (principal, V1)
- T = hora del dato. Vela de 5 min [T, T+5). Si cierre > apertura, compra; si <, vende; si =, nada.
- Entrada al precio de apertura del minuto T+5 (más media horquilla de ese minuto).
- Stop = 0,15 × ATR(14) diario (corte 17:00 NY, días anteriores), comprobado minuto a minuto con
  huecos al precio de apertura del minuto si lo salta.
- Salida a T+180 min o a las 16:55 NY si es antes (FOMC). Sin objetivo, sin BE.
- R = resultado / stop. Coste = horquilla real de entrada y salida (media cada lado) + comisión FTMO
  (FX 0,5 pb, oro 0,3 pb, índices 0) en R.

Variantes (las únicas, 3 en total): V2 salida a T+60; V3 stop 0,30 × ATR.

## Listón (todo sobre V1 agrupada; V2/V3 solo cuentan para el número de pruebas)
1. t neto agrupado (operaciones de los 6 mercados, errores agrupados por día de evento) ≥ 2,4.
2. Neto > 0 en las dos mitades (2011-18 y 2019-26) y con costes ×2.
3. Placebo de hora: la misma regla a la misma hora en días laborables **sin** evento queda claramente
   por debajo (diferencia evento − placebo con t ≥ 2).
4. Placebo de lado: la dirección contraria pierde.
5. Réplica: neto > 0 en al menos 4 de los 6 mercados y en al menos 2 de los 3 tipos de evento.
6. Paseo aleatorio: el mismo código sobre velas de paseo aleatorio da |t| < 2.
7. Correlación diaria con el ORB US100 < 0,3 (solo si pasa lo anterior).
Si falla cualquiera: descartada, sin rescate por subconjuntos.
