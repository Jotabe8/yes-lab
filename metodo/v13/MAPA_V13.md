# Mapa v13: qué queda sin probar para un 2.º sistema (16-11-2026)

Fuentes: registro de 75 familias (metodo/v3/registro_ideas.csv), DIARIO.md, búsquedas v2-v12, revisiones 1 y 2,
darwinex/NUEVAS_VIAS_DARWINEX.md, memoria del proyecto. Condición: ventaja propia, corr < 0,3 con el ORB US100,
operable en MT5 CFD (FTMO/The5ers), futuros NinjaTrader (Lucid) o Darwinex Zero.

## 1. Lo que ya está cerrado (por eje)

| Eje | Probado | Resultado |
|---|---|---|
| Dirección con el propio precio (reversión, momentum, tendencia, RSI, VWAP, NNFX, ML, atlas, 25.000 reglas) | índices, oro, FX, cripto, D1 a M1 | 0/28, casi todo clase A (sin bruto) |
| Calendario (mes, festivo, Halloween, Fed, OPEX, gotobi, nocturna, día semana) | índices, FX | B o C: bruto ≈ coste o sin potencia |
| Eventos (NFP/IPC/FOMC, EIA, 8:30, fix BCE/Londres, subastas del Tesoro) | 6 mercados, bonos | A o B (subastas: vive en el bono nuevo, no en el futuro) |
| Flujos forzados (rebalanceo 60/40, ETF apalancados, pensiones, CTA, roll GSCI) | índices, bonos | A, D, o sin datos |
| Liquidez (choques 5 min, scalping, barridos, noche FX en cruces) | índices, FX | A o B por comisión |
| Datos fuera del precio (GEX, COT, carry, delta QQQ, libros OANDA, NOII) | varios | A, o fuente bloqueada/rechazada |
| Primas de riesgo multi-día (RP, cestas, tendencia, carry, nocturna en futuros) | 28 futuros DZ | beta, no ventaja |
| **ORB incondicional en apertura propia** | GER40, UK100, EU50, FRA40, JP225, HK50, AUS200, oro, crudo, FX, BTC/ETH, US500/US30/US2000 | solo US100; GER40 t 1,58 (C); JP225 y cripto bruto real pero coste (B) |
| ORB en aperturas ajenas, rangos 5-60, SAR, extensiones, zona de ruido | 11 mercados | A o D |

## 2. Huecos que quedan

| Hueco | Base | Datos | Lugar | Veredicto T0 |
|---|---|---|---|---|
| **ORB "en juego" (volumen/rango anómalo en la apertura) en aperturas propias fuera del US100** | Zarattini-Barbon-Aziz 2024: el ORB funciona en los días con volumen relativo alto; aquí solo se probó en acciones (con coste de acciones) | M1 Dukascopy 2012-26 con volumen | FTMO CFD GER40/UK100/oro/JP225; futuros FDXM, MGC | **Prueba 1 (v13)** |
| ORB en ES/RTY/YM (sugerido) | mismo mecanismo | M1 2012-26 | MES/M2K en Lucid | Fuera: misma hora y mismo riesgo que el US100 (corr esperada > 0,6), no diversifica; US500/US30/US2000 incondicional ya falló |
| ORB en CL/GC en futuros (sugerido) | mismo mecanismo | M1 crudo y oro | MCL/MGC | Incondicional ya cerrado (USOIL 8:30/9:30, oro); la versión en juego entra en la prueba 1 |
| ORB JP225 / cripto en lugar más barato | bruto real | sí | no hay lugar a ≤ 0,005 % / ≤ 0,02 % | B, disparador ya anotado |
| Diferenciales de calendario (roll GSCI), carry de curva | flujos forzados | curvas de futuros de pago | DZ | sin datos gratis |
| Desequilibrio de subastas de cierre/apertura (NOII), delta de futuros | flujo informado | Databento (rechazado) | NT/MNQ | bloqueado por Jorge |
| Opciones (prima de volatilidad, 0DTE) | prima de riesgo | — | ninguna prop las ofrece | fuera |
| Small caps | atención minorista | sin datos/prop | — | fuera |

## 3. Prioridad
1. **ORB en juego en aperturas propias (GER40, UK100, JP225, oro COMEX, crudo NYMEX)**: es la única hipótesis
   con mecanismo publicado, datos en mano, lugar barato (GER40 0,0052 %) y que **cambia la muestra** respecto a
   lo ya cerrado (subconjunto de días), no solo los parámetros. Dos variantes (volumen, rango), preregistradas.
2. Si cae, no queda ninguna hipótesis con las tres patas (mecanismo + datos + lugar). Lo que queda necesita un
   lugar más barato (JP225, ETH) o datos de pago (NOII, curvas): ver plan del informe.
