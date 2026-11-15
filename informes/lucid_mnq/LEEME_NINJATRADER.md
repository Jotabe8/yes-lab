# ORB_MNQ_Lucid en NinjaTrader 8: cómo instalarlo, validarlo y ponerlo en marcha

Es el ORB US100 v018 portado a futuros micro del Nasdaq (MNQ) para una cuenta **LucidFlex 50K**. Misma señal, mismo stop,
mismo filtro de volatilidad, mismo trailing en el reto y el mismo stop a entrada a +2R en la fondeada.

## 1. Instalar

1. Instala **NinjaTrader 8 Desktop** (gratis) y conecta la cuenta de Lucid siguiendo el correo de Lucid
   (NinjaTrader va con su conexión CQG/Tradovate). Necesitas NinjaTrader de escritorio: la versión web no corre estrategias.
2. Copia `ORB_MNQ_Lucid.cs` a `Documentos\NinjaTrader 8\bin\Custom\Strategies\`.
3. En NinjaTrader: *New → NinjaScript Editor*, abre la estrategia y pulsa **F5** (compilar).
   No he podido compilarlo aquí: si sale algún error, mándame el texto y lo corrijo.

## 2. Validar antes de usarlo (equivale al Strategy Tester de MT5)

1. *New → Strategy Analyzer*. Estrategia `ORB_MNQ_Lucid`, instrumento **MNQ** (contrato actual; NinjaTrader une los
   anteriores), **1 Minute**, plantilla de horario **CME US Index Futures ETH**.
2. Fechas: **01/01/2022 a hoy** (el filtro de volatilidad necesita unos 6 meses de velas diarias para empezar a actuar).
3. Parámetros: **Modo validación = True**, Fase = 0. Comisión 0.
4. Ejecuta. El EA escribe `Documentos\NinjaTrader 8\ORB_MNQ\ORB_MNQ_Backtest_ops.csv`.
5. Pásamelo (o déjalo en la carpeta de Prop Firm Challenges) y lo comparo con la réplica Python con `comparar_nt.py`.
   Lo doy por bueno con ≥ 95 % de días comunes, ≥ 95 % de días con el mismo lado y correlación ≥ 0,9 (como hicimos con el GER40 en MT5).
   Repite con **Fase = 2** para comprobar el stop a entrada a +2R.

## 3. Ponerlo en marcha en la cuenta de Lucid

- Gráfico o pestaña *Strategies* con **MNQ** del contrato actual, **1 minuto**, **Days to load = 420**.
- **Start behavior: Wait until flat.** Cuenta: la de Lucid (no Sim101).
- Parámetros de la evaluación: Fase **0**, Saldo inicial 50000, Suelo MLL **48000** (o el que muestre el panel), Mejor día 0,
  Riesgo **350 $**, todo lo demás por defecto.
- El PC tiene que estar encendido de **15:25 a 21:35 hora de Madrid** (9:25-15:35 Nueva York), igual que para MT5.
- Al superar el reto el EA escribe "RETO SUPERADO" y deja de operar. En la cuenta fondeada: Fase **2**, Suelo MLL el del panel,
  y borra `ORB_MNQ_<cuenta>_estado.txt` de la carpeta `ORB_MNQ` (es de la cuenta anterior).
- Cambio de contrato (marzo, junio, septiembre, diciembre): NinjaTrader avisa; cambia la estrategia al contrato nuevo ese día
  con la posición cerrada. El estado (suelo, mejor día) se guarda por cuenta, no por contrato.
- Los retiros los pides tú en el panel de Lucid: hace falta tener 5 días con ≥ 150 $ en el ciclo; se cobra el 50 % del
  beneficio hasta 2.000 $, mínimo 500 $, al 90 %.

## 4. Qué compra en Lucid

- **LucidFlex 50K, pérdida diaria (DLL) ACTIVADA y consistencia 40 %** (es la combinación más barata). La DLL es "blanda" y,
  con una operación al día y 350 $ de riesgo, no llega a actuar. Además activa los retiros a demanda.
- España no está en la lista de países restringidos (support.lucidtrading.com, 14/11/2026).

## 5. Lo que el EA no hace

- No pide retiros ni sabe si Lucid te ha pasado la cuenta: el suelo del MLL lo calcula él al cierre de cada día a partir del
  saldo, pero si arrancas a mitad de reto pon el suelo y el mejor día que muestra el panel.
- No hay avisos al móvil (NinjaTrader no tiene push como MT5). Los mensajes salen en la ventana *Output* y las operaciones en
  `ORB_MNQ_<cuenta>_ops.csv`.
