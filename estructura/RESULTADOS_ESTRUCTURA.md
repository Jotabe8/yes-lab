# Opción B: ventaja de las reglas de la prop (2026-11-13)

Pregunta: ¿qué EV por cuota da un EA intradía SIN ventaja de mercado (operación US100 con TP/SL, probabilidad justa, coste 1 punto con stop de 100 puntos = 0,01 R) por la forma de pago del 2-Step de FTMO (pierdes la cuota; cobras el 80 % de los meses buenos y la cuenta perdida no es tuya)?
Simulador: estructura/sim_estructura.py (reto +10 %, verificación +5 %, diaria 5 %, total 10 %, sin límite de tiempo; fondeada 12 meses con retiro cada 10 días hábiles, cuota devuelta). 100K, cuota 540 €. 100.000 simulaciones.

| Política (reto / verificación / fondeada) | P(pasar) | EV por cuota |
|---|---|---|
| Sin ventaja 1 % / 1 % / 1 %, 1:1 | 0,28 | +1.350 € |
| Sin ventaja 2 % / 2 % / 1,5 %, 1:1 | 0,31 | +1.740 € |
| Sin ventaja "audaz" 4,5 % en todo | 0,32 | +1.920 € |
| Sin ventaja audaz, coste 0,03 / 0,05 R | 0,29 / 0,27 | +1.450 / +1.080 € |
| ORB v018 real 2 % / 2 % / 1,5 % (mismo simulador) | 0,39 | +5.820 € |
| ORB v018 con media 0 (control) | 0,28 | +1.880 € |

Conclusiones:
1. La ventaja de estructura existe: unos +1.300-1.900 € por cuota de 100K (≈ 2,5-3,5 veces la cuota) sin ninguna ventaja de mercado, siempre que el coste por operación sea bajo (US100 con stop ancho). Coincide con el control del método (ORB con media 0).
2. El ORB da 3 veces más por cuota (+5.800 €). Con un presupuesto limitado de cuotas, cada euro rinde más en el ORB. La estructura solo suma cuando ya no se pueden abrir más cuentas del ORB (tope de 400.000 $ fondeados por trader/estrategia en FTMO, "una estrategia por usuario" en E8).
3. Las normas de FTMO lo limitan: "Forbidden trading practices" prohíbe el "unrealistic trading (overleveraging, overexposure, one-sided bets, account rolling)" y las posiciones mucho mayores que las habituales; la consecuencia puede ser perder los retiros. La versión audaz (4,5 %) queda descartada; a riesgo normal (1-2 %) y con entradas con lógica (no al azar) el riesgo de normas es menor, pero no nulo.
4. Ojo: este simulador no tiene en cuenta el tiempo. Con el ORB, bajar el riesgo del reto sube el EV por cuota (1,5 %: +7.200 €) porque pasa más a menudo, pero tarda mucho más. Eso ya se optimizó con calendario en plan_12m.py (2 % / 1,5 %); no se cambia.

Veredicto: no merece un EA propio ahora. Se guarda como plan para cuando el ORB llegue al tope de cuentas: un EA intradía de bajo coste en US100 al 1-1,5 % por operación, en cuentas aparte.
Fuente normas: https://ftmo.oanda.com/forbidden-trading-practices/ (consultada 2026-11-13).
