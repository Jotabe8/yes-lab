# Amplitud de apertura (71 acciones) para operar US100/US500/US30: DESCARTADO en P1 (13-11-2026)

Ajuste 2018-2022, entrada 9:35 y salida 15:55 NY, R = 0,25 × ATR14 diario, coste con horquilla real Dukascopy.

| Variante | Ops/año | Bruto R | Coste R | Neto R | t | Placebo p95 |
|---|---|---|---|---|---|---|
| Estrecho (contra) US100 | 22 | −0,218 | 0,035 | −0,253 | −1,1 | +0,398 |
| Estrecho US500 | 4 | −0,020 | 0,056 | −0,076 | −0,1 | +0,919 |
| Estrecho US30 | 9 | +0,219 | 0,027 | +0,191 | +0,5 | +0,668 |
| Amplio (a favor) US100 | 87 | +0,001 | 0,036 | −0,035 | −0,2 | +0,227 |
| Amplio US500 | 105 | −0,021 | 0,055 | −0,075 | −0,6 | +0,218 |
| Amplio US30 | 101 | −0,019 | 0,027 | −0,046 | −0,4 | +0,215 |

- Los movimientos "estrechos" son raros (4-22 al año) y no se deshacen: en US100 siguen (−0,22 R al
  ir en contra). No pasa P0 por frecuencia ni P1 por señal.
- Los "amplios" no continúan más que un día cualquiera: bruto ≈ 0 en los tres índices.
- El coste no es el problema (0,03-0,06 R): falta señal. Fuera de muestra sin abrir.
Script `amplitud.py`, salida `amplitud_salida.txt`. Datos índices: `descargar-indices-m1.yml`.
