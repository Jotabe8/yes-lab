# EA v018 para las cuentas nuevas (FTMO Black Friday y The5ers en enero)

## Qué ha cambiado en el EA

`ORB_US100_AGR_v018.mq5`: **un único cambio**. En demo o real el CSV de operaciones se llama ahora
`ORB_AGR_v018_live_<nº de cuenta>.csv` en vez de `ORB_AGR_v018_live.csv`. Así dos o tres cuentas en el mismo PC
(que comparten `Common\Files`) no mezclan sus operaciones. El CSV del Strategy Tester no cambia. Todo lo demás es
idéntico, línea por línea, al v018 que corre en la 1-Step.

Pasos:
1. Copia `ORB_US100_AGR_v018.mq5` a `MQL5\Experts\` de **cada** instalación nueva de MT5 y compílalo (F7 en MetaEditor).
2. La 1-Step actual puede seguir con su .ex5 de siempre. Si la recompilas, su CSV pasará a llamarse
   `ORB_AGR_v018_live_531498006.csv` (el script `estado_mt5.ps1` ya copia todos los `ORB_*.csv`, no hay que tocarlo).

## .set (cárgalos en *Entradas → Cargar*)

| Firma y fase | Archivo |
|---|---|
| FTMO 2-Step Swing 10K, Fase 1 (2 %) | `ORB_v018_FTMO_2Step_10K_fase1.set` |
| FTMO 2-Step Swing 10K, Fase 2 (2 %) | `ORB_v018_FTMO_2Step_10K_fase2.set` |
| FTMO 2-Step Swing 10K, fondeada (1,5 %, stop a entrada a +2R) | `ORB_v018_FTMO_2Step_10K_fondeada.set` |
| The5ers High Stakes 10K, Step 1 | `ORB_v018_The5ers_HighStakes_10K_fase1.set` |
| The5ers High Stakes 10K, Step 2 | `ORB_v018_The5ers_HighStakes_10K_fase2.set` |
| The5ers High Stakes 10K, fondeada | `ORB_v018_The5ers_HighStakes_10K_fondeada.set` |

Todos: modelo 2-Step, tamaño 10.000, filtro de volatilidad p90, simulador apagado, avisos push encendidos.
Diferencias de The5ers: 3 días mínimos (en vez de 4), riesgo 0,6 % tras llegar al objetivo (para que un día de +1R ya
cuente como "día rentable" de ≥ 0,5 %) y cierre del FOMC a las 20:55 servidor (The5ers no deja poner órdenes de 2 min
antes a 2 min después de una noticia fuerte).

## Antes de arrancar en The5ers (enero)

1. **Hora del servidor.** El EA abre el rango a las 16:30 de servidor, que en FTMO son las 9:30 de Nueva York todo el año.
   En el MT5 de The5ers abre un gráfico M1 de NAS100 en un día de dato de las 8:30 NY (por ejemplo, el IPC): la vela grande
   debe salir a las 15:30 de servidor. Si sale a otra hora, dímelo y cambio `InpSessionStart`, `InpTradeEnd`, `InpFlatTime`
   y `InpFomcServerHHMM` en los .set. Mira también una fecha de marzo entre el cambio de hora de EE. UU. y el de Europa.
2. **Días rentables.** The5ers exige 3 días con ≥ 0,5 % de beneficio cerrado; el EA cuenta días con operación. Si el EA dice
   "FASE SUPERADA" y el panel de The5ers no, pon `InpMinTradingDays = 10` y reinícialo: seguirá al 0,6 % hasta tenerlos.
3. Su EA tiene que llevar el stop visible en la orden (el v018 lo hace) y tú tener el código fuente (lo tienes).
