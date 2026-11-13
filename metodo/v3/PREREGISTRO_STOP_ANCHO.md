# Preregistro v3 · Stop más ancho en las dos clase B con señal real (13-11-2026, antes de ver datos)

Motivo: en JP225 (apertura de Tokio) y ETH (apertura de NY) el bruto es real (t 3,3 / 3,5) pero el coste en la
cuenta FTMO es 0,09 R / 0,15-0,2 R porque el stop es corto (0,15 ATR). Un stop más ancho divide el coste en R;
la duda es cuánto edge se pierde. Misma regla de entrada y salida; solo cambia el stop:
- V1: stop 0,30 × ATR(14) de sesión.
- V2: stop en el extremo opuesto del rango de apertura (JP225 primera barra de 30 min; ETH rango de 10 min), con un mínimo de 0,10 ATR.
Coste: horquilla real FTMO (JP225 0,0157 %; ETH 0,025 % + comisión 0,065 % ida y vuelta). Precio medio, M1 Dukascopy 2018-2026.
4 pruebas (2 variantes × 2 mercados). Pasa una si: t neto 2018-26 ≥ 2,5; segunda mitad > 0; costes ×2 > 0;
supera al lado contrario con la misma salida. ETH se juzga en 2021-03 → 2026-11 (horquilla de Dukascopy usable).
