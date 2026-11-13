# Preregistro: deriva nocturna en la apertura europea (13-11-2026)

Mecanismo (Boyarchenko, Larsen y Whelan 2023, "The Overnight Drift", RFS): los intermediarios acaban la sesión
de EE. UU. con inventario comprado a clientes que venden; lo descargan cuando vuelve la liquidez con la apertura
europea, y el precio de los futuros de índices US sube sobre todo entre la 1:00 y las 4:00 de Nueva York, más
tras días de caída. Distinto de la "prima nocturna" ya descartada (cierre → apertura, cruza el swap de las 17:00):
aquí la operación abre y cierra entre las 17:00 y las 9:30 de NY, así que **no paga swap** en FTMO, y no coincide
con el ORB (correlación esperada baja).

Reglas (fijas): largo US100, US500, US30. V1: entrada 1:00 NY, salida 4:00 NY, todos los días hábiles.
V2: igual, solo si la sesión de contado anterior (9:30 → 16:00) cerró en negativo.
Coste: horquilla real Dukascopy a esas horas. R = 0,25 × ATR14 de sesión.
Ajuste 2012-2022, fuera de muestra 2023-2026. Listón flexible (Jorge, 13-11): t ≥ 2 en ajuste, OOS > 0,
neto con coste real > 0 y EV por cuota > control; corr con ORB < 0,3. Placebo: misma ventana desplazada (12:00-15:00 NY del día).
