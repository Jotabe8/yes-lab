# Futuros de Darwinex Zero: lista real y consecuencias (13-11-2026)

Fuente: tabla de activos de darwinexzero.com/es/activos (pestaña Futuros, leída el 13-11-2026 con el navegador).
Comisión en USD (EUR en Eurex) por contrato y orden. Cuenta de futuros: MT5, 1.000.000 $ virtuales.

| Tipo | Contratos | Comisión |
|---|---|---|
| Índices | ES, NQ, RTY, YM (E-mini; **sin micros**) | 4 |
| Índices Eurex | FDAX, FESX | 3 € |
| Bonos | ZN (10 años EE. UU.), FGBL (Bund) | 3 |
| Divisas | 6A, 6B, 6C, 6E, 6J, 6N, 6S | 2,5 |
| Metales | GC, SI, HG, PL | 3 |
| Energía | CL, BZ, HO, RB, NG | 3 |
| Agrícolas y carne | ZC, ZS, ZL, ZM, KE, HE, LE | 3 |
| Cripto | **solo MBT (Bitcoin micro, 0,1 BTC)** | 3 |

**No hay** BTC estándar, ETH (ni MET), MNQ/MES, Nikkei (NKD/NIY), ZT/ZF/ZB.

CFD de cripto (cuenta aparte, 100.000 $, apalancamiento 1:1): **0,05 % de comisión por orden** (0,10 % ida y vuelta)
y horquilla BTC ~11 $. CFD de índices: NDX horquilla 0,9 puntos, 2,75 $ por orden y contrato (10 × NDX), swap largo
−45,29 $/día por contrato. Oro CFD 0,46 puntos + 0,0025 %.

## Consecuencias

1. **El ORB cripto NO es operable en Darwinex Zero.** Con MBT, el coste es ~0,19 R por operación (3 $ por orden más el tick,
   frente a ~35 $ de riesgo por contrato): neto 2021-26 ≈ +0,05 R, t < 1. Con el CFD de cripto (0,10 % ida y vuelta), peor
   que en FTMO. Vuelve a ser clase B; disparador sin cambios (BTC/ETH ≤ 0,02 % ida y vuelta o contrato estándar).
2. **El ORB US100 se puede correr en cualquiera de las dos cuentas.** NQ: ~0,01 R de coste. CFD NDX: 0,9 puntos + 5,5 $ por
   ida y vuelta ≈ 0,6 pb, igual que FTMO (0,5 pb). Sin el ORB cripto, la cuenta de futuros no aporta nada: **la cuenta CFD
   (45 €/mes) es la recomendada.**
3. **Cruce con las clases B del registro:** ninguna se vuelve operable. JP225 (no hay Nikkei), gotobi en 6J (6J cuesta lo
   mismo que el CFD), ORB GER40 en FDAX (su problema no era el coste, era t 1,58), víspera de festivo en ES (9 ops/año).
4. **Subastas del Tesoro dentro del día (ZN):** descartado en T0. El tick del ZN (1/64 = 1,56 pb) más 6 $ de comisión
   suman ~2,2 pb por ida y vuelta; harían falta ≥ 4,4 pb de efecto en el día, y el ciclo entero de 10 días en futuros solo
   dio +3 pb. Además el efecto vive en el bono recién emitido, no en el futuro.
