# Preregistro: variantes del mecanismo ORB (giro elegido por Jorge 2026-11-13)

Base: réplica v018 (rango 10 min, stop 0,15 ATR14, salida 15:55). Mercados US100, US500, US30. M1 bid/ask Dukascopy 2012-2026.
Variantes (7 pruebas por mercado):
1-5. Rango L = 5, 10 (base), 15, 30 y 60 min.
6. SAR: tras saltar el stop del ORB 10 min, una entrada en contra con el mismo stop hasta 15:55.
7. Cartera US100 + US500 + US30 del ORB 10 min (para otra firma).
Una variante es un sistema nuevo solo si: neto > 0 con t >= 2 en 2012-22 (US30 2014-22), OOS 2023-26 neto > 0, corr diaria con la serie real v018 < 0,5 (0,3 para considerarla descorrelacionada) y EV/cuota de la combinación > solo ORB.
Coste: spread Dukascopy ya incluido en r; se añade 0,6× ese spread como margen de sensibilidad (×2).
