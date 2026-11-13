# ORB de la apertura de NY en BTC y ETH — DESCARTADO por coste y apalancamiento

Réplica ORB (9:30 NY, stop 0,15 ATR de sesión, salida 15:55), días laborables, M1 bid/ask Dukascopy 2018-2026.

- El efecto existe: elegir el lado de la vela del rango supera al lado contrario en casi todas las variantes (BTC rango 10/15/60 min: exceso t 1,6/2,4/2,2 en 2018-22 y 1,0/0,9/1,2 en 2023-26; ETH 60 min t 2,4 y 1,9). Es el mismo mecanismo del ORB US100 (llegada del flujo de EE. UU.).
- Pero el bruto en 2024-26 es ~+0,20 R por operación y el coste lo iguala: Dukascopy 0,18-0,33 R de spread; en FTMO la comisión cripto es 0,0325 % por lado (0,065 % ida y vuelta ≈ 0,17 R con un stop de ~0,37 % del precio) más spread → neto ≈ 0 o negativo.
- Además FTMO limita el apalancamiento en cripto: con ese stop, arriesgar un 1 % exige ~2,7 veces el capital en nominal.

Veredicto: no hay EA posible en FTMO. Solo valdría en un bróker con comisión cripto muy baja y apalancamiento ≥ 1:5.
Fuente comisión: https://ftmo.com/en/blog/ftmo-enhances-crypto-trading-new-instruments-and-better-spreads/
