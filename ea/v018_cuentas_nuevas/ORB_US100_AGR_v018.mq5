//+------------------------------------------------------------------+
//|  ORB_US100_AGR_v018.mq5 - version agresiva por fases              |
//|  Proyecto Prop Firm Challenges - Jorge                            |
//|  Version 0.18 AGR - 25/10/2026                                    |
//+------------------------------------------------------------------+
//
//  NOVEDADES v0.18 (25/10/2026) respecto a v0.17 BUILD I
//  ------------------------------------------------------------------
//   - Filtro de volatilidad extrema (InpVolFilter): no opera el dia en que el ATR(14)
//     diario en % del precio supera su percentil InpVolPct de los ultimos InpVolLookback dias.
//     Validado en Python 2018-2026: R/ano 6,1->8,8 (2018-22) y 27,7->32,2 (2023-26),
//     peor drawdown 51->45 R, ano 2020 -26->-15 R.
//   - Valores por defecto = punto de equilibrio FTMO 2-Step: reto 2 %, fondeada 1,5 %,
//     cuenta 100.000. Fondeada (revisado 25/10/2026 tarde): SIN trailing y stop a entrada
//     a +2 R (InpTrailFunded = false, InpFundedBreakevenR = 2), como la v0.17.
//     Estudio cartera/fondeada_variantes.py (2018-2026, filtro p90, 2-Step 100K, 1,5 %):
//     neto medio/ano +25.157 EUR con BE +2 R frente a +17.488 EUR con trailing 3R/1R;
//     mejor en 2018-22 y en 2023-26. El reto sigue con trailing 3 R / 1 R.
//   - Magic 261018 y CSV propios (ORB_AGR_v018_*.csv).
//  Pensado para la proxima cuenta: FTMO 2-Step tipo Swing (sin restriccion de noticias).
//   - 14/11/2026: el CSV de demo/real se llama ORB_AGR_v018_live_<n. de cuenta>.csv (unico cambio).
//
//  QUE HACE
//  ------------------------------------------------------------------
//  Opening Range Breakout sobre el CFD del Nasdaq (US100 / USTECH100M).
//  Rango de apertura = primeros N minutos tras la apertura cash USA.
//
//  Modo de entrada 0 (por defecto, estilo estudio ORB 5 min en QQQ):
//     - Vela del rango alcista  -> LARGO a mercado al terminar el rango.
//     - Vela del rango bajista  -> CORTO a mercado.
//     - Vela casi sin cuerpo (doji) -> no opera ese dia.
//  Modo de entrada 1 (ruptura clasica):
//     - Buy stop encima del maximo y sell stop debajo del minimo (OCO).
//
//  Stop: modo 0 = extremo opuesto del rango; modo 1 = % del ATR diario.
//  Salida: objetivo en R (opcional) o cierre a la hora de cierre del dia.
//  1 operacion al dia como maximo por defecto.
//
//  PROTECCIONES DE PROP FIRM (mismo esqueleto que el EA anterior)
//   - Freno de perdida diaria y total, tope de beneficio diario (opcional),
//     parar al alcanzar objetivo, dias bloqueados, spread maximo,
//     filtro de noticias USD alto impacto (solo demo/real), cierre forzado,
//     tope de exposicion (nocional) para rangos muy estrechos.
//   - Diagnostico al final del test en el Diario.
//
//  BUILD I (13/10/2026): riesgo del challenge 2 % -> 1,8 % (el 07/02/2025 un stop con
//   1,5 R de deslizamiento a las 17:00 servidor costo el 3,02 %, por encima del 3 % diario).
//   Ademas: si el margen hasta el suelo de perdida maxima no da ni para la
//   mitad del riesgo normal (InpExhaustPct = 50), la cuenta se da por perdida: en real el EA
//   avisa "CUENTA AGOTADA" y deja de operar; en el tester el simulador compra otro challenge.
//   Motivo: el tester 2024-2026 paso 107 dias (5 meses seguidos en 2026) operando nada en una
//   cuenta zombi pegada al suelo.
//
//  BUILD H (09/10/2026): avisos push al movil (arranque, entrada, salida, "hoy no opera"
//   a las 16:45 servidor, frenos, challenge superado) y fechas FOMC/festivos 2027.
//   Si a las 15:50 hora de Espana no ha llegado ningun aviso, el PC o MT5 no estan operando.
//
//  TRAILING EN EL CHALLENGE (BUILD G, 09/10/2026):
//   - Fases de challenge (InpStage 0 y 1): cuando el trade llega a +InpTrailActR R,
//     el stop sigue al maximo a InpTrailDistR R de distancia (por defecto 3 R / 1 R).
//   - Fondeada (InpStage 2): sin trailing; stop a entrada al llegar a +InpFundedBreakevenR R (2 R).
//   - Motivo (estudio 09/10/2026, M1 FTMO 2021-2026): en el challenge el premio esta
//     topado (+10 %) y la Best Day Rule penaliza dias enormes -> pasa 44 % frente a 34 %;
//     en la fondeada los retiros son lineales y el trailing resta.
//   - Challenge: al llegar a +8 % el riesgo baja al 1 % (InpNearTargetPct / InpNearTargetRiskPct).
//   - Sobrevive a reinicios: la distancia de riesgo se recalcula con el ATR diario y
//     el maximo favorable con las velas M1 desde la apertura de la posicion.
//
//  MODO FTMO 1-STEP (BUILD F, 09/10/2026) - parametro InpModel:
//   1 = 1-Step: una fase (+10 %), perdida diaria 3 %, perdida maxima 10 %
//       TRAILING desde el balance de cierre mas alto (nunca baja; se reinicia
//       tras un retiro) y Best Day Rule (mejor dia <= 50 % del beneficio de
//       los dias positivos) para pasar y para cobrar.
//   2 = 2-Step: como antes (10 % + 5 %, diaria 5 %, maxima 10 % estatica, 4 dias).
//   Fases con 1-Step: InpStage 0 = challenge, 2 = fondeada (1 no existe).
//
//  VERSION AGRESIVA v0.17 (27/09/2026) - misma senal que v0.16
//   - Riesgo por fase: Fase 1 y Fase 2 al 2 %, cuenta fondeada al 0,75 %.
//     Objetivo: pasar el challenge en 2-3 meses y cobrar pronto.
//   - Colchon: ninguna operacion puede dejar la cuenta a menos del 0,5 %
//     del limite de perdida total o diaria de la firma (reduce el lote).
//   - Al alcanzar el objetivo (10 % / 5 %) sigue con lote minimo hasta
//     cumplir los dias minimos de trading y luego se detiene.
//   - SIMULADOR (solo tester, InpAutoStages): encadena Fase 1 -> Fase 2 ->
//     fondeada -> retiros cada 14 dias; si una cuenta falla "compra" otra.
//     Al final imprime cuotas pagadas, retiros y neto. Usar deposito grande
//     (p. ej. 1.000.000) y Tamano nominal = tamano del challenge (10000).
//
//  NOVEDADES v0.16 (27/09/2026)
//   - Salida antes de noticias USD de alto impacto (calendario MT5 en
//     demo/real) y antes del FOMC (fechas 2024-2026 en el codigo, tambien
//     en el tester). No cierra dentro de los 2,5 min previos (regla FTMO).
//   - Control por PF movil (DESACTIVADO por defecto desde el backtest del
//     27/09/2026: con 30 % de aciertos, un PF de 60 operaciones por debajo
//     de 0,9 aparece en el 97 % de las trayectorias aunque el edge sea
//     real; en 2024 habria parado el EA en octubre con PF anual 1,55).
//   - En el tester, el PF movil, el PnL_neto y la R ignoran la comision
//     (InpCommInTester = false) porque el tester de FTMO cobra ~1.660 $
//     por lote y lado en US100.cash. En demo/real siempre se cuenta.
//   - CSV ampliado para el forward test: riesgo, R, comision real,
//     slippage de entrada y de stop, PF movil. Fichero nuevo:
//     ORB_live_v16.csv / ORB_backtest_v16.csv (carpeta Common\Files).
//
//  AVISO: esqueleto sin validar. Flujo: backtest -> fuera de muestra ->
//  60 dias demo -> challenge.
//
//  TESTER: simbolo US100/USTECH100M, M5, "Every tick based on real ticks",
//  deposito 100000 USD (lote minimo 1 en USTECH100M), apalancamiento 1:30.
//+------------------------------------------------------------------+
#property copyright "Proyecto Prop Firm Challenges - Jorge"
#property version   "0.17"
#property description "ORB US100 v0.18 - filtro de volatilidad - FTMO 2-Step"

#include <Trade\Trade.mqh>

input group "1. Riesgo por fase (version agresiva)"
input int    InpModel             = 2;      // Tipo de challenge FTMO: 1 = 1-Step, 2 = 2-Step
input int    InpStage             = 0;      // Fase de esta cuenta: 0 = Challenge / Fase 1, 1 = Fase 2 (solo 2-Step), 2 = Fondeada
input double InpAccountSize       = 100000;  // Tamano nominal del challenge (OBLIGATORIO, p. ej. 10000)
input double InpRiskP1Pct         = 2.0;    // % de riesgo por trade en Fase 1 (1.8: con un deslizamiento de 1.5 R la perdida queda en 2.7 %, por debajo del 3 % diario)
input double InpRiskP2Pct         = 2.0;    // % de riesgo por trade en Fase 2
input double InpRiskFundedPct     = 1.5;   // % de riesgo por trade en la cuenta fondeada
input double InpTargetP1Pct       = 10;     // Objetivo Fase 1 %
input double InpTargetP2Pct       = 5;      // Objetivo Fase 2 %
input int    InpMinTradingDays    = 4;      // 2-Step: dias minimos de trading por fase (FTMO: 4)
input double InpRiskAfterTargetPct = 0.25;  // 2-Step: riesgo % tras alcanzar el objetivo mientras faltan dias minimos
input double InpFirmDaily1StepPct = 3.0;    // 1-Step: limite REAL de perdida diaria de la firma %
input double InpBestDayPct        = 50;     // 1-Step: el mejor dia no puede superar este % del beneficio de los dias positivos
input double InpFirmMaxLossPct    = 10;     // Limite REAL de perdida total de la firma %
input double InpCushionPct        = 0.5;    // Colchon: ninguna operacion puede dejar la cuenta a menos de X % del limite
input double InpMaxNotionalX      = 20.0;   // Exposicion maxima = X veces la cuenta (0 = off; FTMO indices 1:50)
input double InpTargetR           = 0;      // Objetivo en R (0 = sin objetivo, cierra a la hora de cierre)
input double InpBreakevenR        = 0;      // Mover stop a entrada al ganar X R en todas las fases (0 = off)
input bool   InpTrailChallenge    = true;   // Trailing stop en el challenge (fases 0 y 1)
input bool   InpTrailFunded       = false;  // Trailing stop tambien en la fondeada (v0.18)
input double InpTrailActR         = 3.0;    // Trailing: se activa al ganar X R
input double InpTrailDistR        = 1.0;    // Trailing: distancia del stop al maximo, en R
input double InpTrailStepR        = 0.1;    // Trailing: solo modifica el stop si mejora al menos X R (evita cientos de modificaciones)
input double InpNearTargetPct     = 8.0;    // Challenge: al llegar a +X % de beneficio, bajar el riesgo (0 = off)
input double InpNearTargetRiskPct = 1.0;    // Challenge: riesgo % cuando ya se esta cerca del objetivo
input double InpExhaustPct        = 50;     // Cuenta agotada: si el margen hasta el suelo es menor que X % del riesgo normal, se da por perdida (0 = off)
input bool   InpPush              = true;   // Notificaciones push al movil (MT5: Herramientas > Opciones > Notificaciones, MetaQuotes ID)
input double InpFundedBreakevenR  = 2;      // Fondeada: stop a entrada al ganar X R (0 = off)

input group "2. Senal ORB"
input int    InpORMinutes         = 10;     // Minutos del rango de apertura (5, 15, 30...)
input int    InpEntryMode         = 0;      // Modo entrada: 0 = direccion de la vela del rango, 1 = ruptura con ordenes stop
input double InpMinBodyPct        = 10;     // Modo 0: cuerpo minimo en % del rango (menos = doji, no opera)
input double InpBreakBufferPts    = 0;      // Modo 1: margen en puntos por encima/debajo del rango
input int    InpStopMode          = 1;      // Stop: 0 = extremo opuesto del rango, 1 = % del ATR diario
input double InpStopDailyAtrPct   = 15;     // Stop modo 1: % del ATR diario (14)
input double InpMinRangeAtrPct    = 0;      // Rango minimo en % del ATR diario (0 = off)
input double InpMaxRangeAtrPct    = 0;      // Rango maximo en % del ATR diario (0 = off)
input bool   InpVolFilter         = true;   // v0.18: no operar con volatilidad extrema
input double InpVolPct            = 90;     // ...si el ATR% diario supera este percentil
input int    InpVolLookback       = 252;    // ...de los ultimos X dias
input bool   InpTrendFilter       = false;  // Solo a favor de la EMA H1 (largos encima, cortos debajo)
input int    InpTrendEmaPeriod    = 200;    // Periodo EMA H1 del filtro de tendencia
input bool   InpAllowLong         = true;   // Permitir largos
input bool   InpAllowShort        = true;   // Permitir cortos

input group "3. Horario (hora del servidor, HHMM)"
input int    InpSessionStart      = 1630;   // Apertura cash USA en hora del servidor (FTMO/MetaQuotes: 16:30)
input int    InpTradeEnd          = 2200;   // Ultima hora para entrar / anular ordenes pendientes
input int    InpFlatTime          = 2230;   // Cierra todo a esta hora
input int    InpMaxEntryDelayMin  = 5;      // Si el rango termino hace mas de X min (EA cargado tarde, reinicio), no entra ese dia

input group "4. Reglas prop firm (frenos internos)"
input double InpDailyLossPct      = 4.5;    // Freno perdida diaria % (la firma suele ser 5%)
input double InpMaxLossPct        = 9.5;    // Freno perdida total % desde el inicio de la fase (la firma suele ser 10%)
input double InpDailyProfitCapPct = 0;      // Deja de operar al ganar X% en el dia (0 = off)
input double InpStopAtTargetPct   = 0;      // Parar al alcanzar objetivo challenge, p.ej. 10 (0 = off)
input int    InpMaxTradesDay      = 1;      // Max trades por dia
input int    InpMaxSpreadPoints   = 0;      // Spread maximo en puntos al entrar (0 = off)
input double InpFirmDailyLossPct  = 5.0;    // Limite REAL de la firma (solo para estadisticas)

input group "5. Noticias y dias bloqueados"
input bool   InpNewsFilter        = false;  // Filtro de entrada por noticias USD (DESACTIVADO: FTMO permite noticias en el challenge y el backtest no lo tenia)
input int    InpNewsPreSessionMin = 5;      // Bloquea la entrada si hay noticia desde X min antes de la apertura (16:25 servidor)...
input int    InpNewsPostEntryMin  = 10;     // ...hasta X min despues de la entrada (16:50 servidor)
input string InpNewsExclude       = "EIA;Crude;Natural Gas;Baker Hughes;Member"; // Noticias USD que se ignoran (texto en el nombre, separado por ;)
input bool   InpNewsExit          = false;  // Cerrar posicion antes de noticia USD alto impacto (DESACTIVADO; el FOMC se cierra aparte)
input int    InpNewsExitMinBefore = 5;      // Minutos antes de la noticia para cerrar (minimo 3)
input bool   InpFomcClose         = true;   // Cerrar antes del FOMC (fechas en codigo, funciona en el tester)
input int    InpFomcServerHHMM    = 2100;   // Hora del FOMC en hora del servidor (14:00 NY = 21:00 FTMO)
input string InpExtraDates        = "";     // Dias extra sin operar AAAA.MM.DD separados por coma (festivos USA 2024-2026 ya incluidos)

input group "6. Control de rendimiento (PF movil)"
input bool   InpPfControl         = false;  // Ajustar riesgo segun el PF movil (DESACTIVADO: con 60 ops es ruido, ver estado del proyecto)
input int    InpPfWindow          = 60;     // Operaciones que cuenta el PF movil
input int    InpPfMinTrades       = 40;     // No actua hasta tener este numero de operaciones
input double InpPfReduceBelow     = 1.0;    // Si el PF movil baja de aqui -> riesgo reducido
input double InpRiskReducedPct    = 0.3;    // Riesgo reducido % por trade
input double InpPfHaltBelow       = 0.9;    // Si el PF movil baja de aqui -> deja de abrir (hay que reiniciar a mano)
input bool   InpCommInTester      = false;  // Contar comisiones en el tester (el tester de FTMO cobra una comision irreal en US100.cash)

input group "7. Otros"
input long   InpMagic             = 261018; // Numero magico
input bool   InpLogCsv            = true;   // Registrar trades cerrados en CSV

input group "8. Simulador de challenges (solo tester)"
input bool   InpAutoStages        = true;   // En el tester: encadenar fases, retiros y recompras
input double InpSimFee            = 489;    // Cuota de cada challenge en $ (FTMO 2-Step 100K = 439 EUR ~ 489 $)
input int    InpPayoutDays        = 14;     // Dias entre retiros en la fondeada
input double InpPayoutSplit       = 80;     // 2-Step: % del beneficio que cobra el trader
input double InpPayoutSplit1Step  = 90;     // 1-Step: % del beneficio que cobra el trader (sin reembolso de cuota en la simulacion)

//--- Globales
CTrade   trade;
double   g_size = 0;
int      hAtrD = INVALID_HANDLE, hEma = INVALID_HANDLE;
datetime g_skip[];
// Festivos y cierres anticipados de la bolsa USA 2024-2026 (en el codigo: el tester corta los textos largos)
string US_HOLIDAYS[] = {
   "2024.01.01",
   "2024.01.15",
   "2024.02.19",
   "2024.03.29",
   "2024.05.27",
   "2024.06.19",
   "2024.07.03",
   "2024.07.04",
   "2024.09.02",
   "2024.11.28",
   "2024.11.29",
   "2024.12.24",
   "2024.12.25",
   "2025.01.01",
   "2025.01.09",
   "2025.01.20",
   "2025.02.17",
   "2025.04.18",
   "2025.05.26",
   "2025.06.19",
   "2025.07.03",
   "2025.07.04",
   "2025.09.01",
   "2025.11.27",
   "2025.11.28",
   "2025.12.24",
   "2025.12.25",
   "2026.01.01",
   "2026.01.19",
   "2026.02.16",
   "2026.04.03",
   "2026.05.25",
   "2026.06.19",
   "2026.07.03",
   "2026.09.07",
   "2026.11.26",
   "2026.11.27",
   "2026.12.24",
   "2026.12.25",
   "2027.01.01",
   "2027.01.18",
   "2027.02.15",
   "2027.03.26",
   "2027.05.31",
   "2027.06.18",
   "2027.07.05",
   "2027.09.06",
   "2027.11.25",
   "2027.11.26",
   "2027.12.24"
};
datetime g_lastBar = 0;
datetime g_curDay  = 0;
double   g_dayStartBalance = 0;
int      g_tradesToday = 0;
bool     g_dayLocked   = false;
bool     g_totalLocked = false;
bool     g_rangeDone   = false;   // ya se evaluo el rango hoy
bool     g_beDone      = false;
bool     g_exhausted   = false;   // CalcLots: margen hasta el suelo insuficiente (cuenta agotada)
double   g_mfe         = 0;       // maximo favorable del trade abierto (en precio)
ulong    g_mfeTicket   = 0;       // posicion a la que corresponde g_mfe
int      d_trailMods   = 0, d_beMods = 0, d_exhausted = 0;
double   g_riskDist    = 0;       // distancia de stop inicial del trade/orden de hoy
datetime g_fomcDays[];
int      g_stage = 0;                    // 0 = Fase 1, 1 = Fase 2, 2 = fondeada
double   g_base  = 0;                    // balance al inicio de la fase (o tras el ultimo retiro simulado)
int      g_tradeDays = 0;                // dias con operaciones en la fase actual
datetime g_lastTradeDay = 0;
bool     g_targetHit = false;
datetime g_lastPayoutDay = 0;
bool     g_refundPending = false;
double   g_peak = 0;                    // 1-Step: balance de cierre mas alto (base del trailing)
double   g_firmDaily = 5.0;             // limite diario real de la firma segun el modelo
double   g_bestDay = 0, g_posDays = 0, g_todayPnl = 0;   // 1-Step: Best Day Rule
datetime g_pnlDay = 0;
bool     g_bdWarned = false;
double   g_bdTmp1 = 0, g_bdTmp2 = 0;
// estadisticas del simulador
int      sim_bought = 0, sim_p1 = 0, sim_p2 = 0, sim_fail = 0, sim_payN = 0;
double   sim_paySum = 0, sim_fees = 0;
datetime sim_firstPay = 0, sim_firstFunded = 0;
double   g_curRiskPct  = 0;       // riesgo vigente (puede reducirlo el PF movil)
double   g_pf          = 0;       // PF movil
int      g_pfTrades    = 0;
bool     g_pfHalt      = false;
double   g_expEntry    = 0;       // precio esperado de entrada (para slippage)
double   g_tradeRiskPct = 0, g_tradeRiskMoney = 0;
double   g_inPrice = 0, g_inSlipPts = 0, g_inComm = 0;
// Anuncios FOMC 2024-2027 (14:00 hora de Nueva York; 2027 = calendario provisional de la Fed, consultado el 09/10/2026)
string FOMC_DATES[] = {
   "2024.01.31","2024.03.20","2024.05.01","2024.06.12","2024.07.31","2024.09.18","2024.11.07","2024.12.18",
   "2025.01.29","2025.03.19","2025.05.07","2025.06.18","2025.07.30","2025.09.17","2025.10.29","2025.12.10",
   "2026.01.28","2026.03.18","2026.04.29","2026.06.17","2026.07.29","2026.09.16","2026.10.28","2026.12.09",
   "2027.01.27","2027.03.17","2027.04.28","2027.06.09","2027.07.28","2027.09.15","2027.10.27","2027.12.08"
};

// estadisticas reglas firma
double   g_dayWorstDD = 0, g_worstDailyDD = 0, g_minEquity = 0;
int      g_breachDays = 0, g_days = 0;

// diagnostico
int d_days = 0, d_skip = 0, d_range = 0, d_size = 0, d_doji = 0, d_side = 0,
    d_trend = 0, d_news = 0, d_spread = 0, d_lots = 0, d_orders = 0, d_fills = 0, d_overnight = 0, d_closefail = 0,
    d_newsexit = 0, d_pfreduced = 0, d_pfhalt = 0, d_late = 0;

//+------------------------------------------------------------------+
int HHMM(datetime t) { MqlDateTime s; TimeToStruct(t, s); return s.hour * 100 + s.min; }
datetime DayOf(datetime t) { return (datetime)((long)t - ((long)t % 86400)); }
datetime AtHHMM(datetime day, int hhmm) { return day + (hhmm / 100) * 3600 + (hhmm % 100) * 60; }

double RoundToTick(double price)
{
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(ts <= 0) return NormalizeDouble(price, _Digits);
   return NormalizeDouble(MathRound(price / ts) * ts, _Digits);
}

//+------------------------------------------------------------------+
int OnInit()
{
   // proteccion: este EA solo esta pensado para el Nasdaq 100
   string sym = _Symbol;
   StringToUpper(sym);
   if(StringFind(sym, "100") < 0 && StringFind(sym, "NAS") < 0 && StringFind(sym, "USTEC") < 0 && StringFind(sym, "NDX") < 0)
   {
      PrintFormat("ERROR: simbolo %s no es el Nasdaq 100. Elige US100.cash / USTECH100M en el tester.", _Symbol);
      return INIT_PARAMETERS_INCORRECT;
   }

   hAtrD = iATR(_Symbol, PERIOD_D1, 14);
   hEma  = iMA(_Symbol, PERIOD_H1, InpTrendEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(hAtrD == INVALID_HANDLE || hEma == INVALID_HANDLE)
   {
      Print("Error creando indicadores");
      return INIT_FAILED;
   }

   ArrayResize(g_skip, 0);
   for(int h = 0; h < ArraySize(US_HOLIDAYS); h++)
   {
      int k = ArraySize(g_skip);
      ArrayResize(g_skip, k + 1);
      g_skip[k] = DayOf(StringToTime(US_HOLIDAYS[h]));
   }
   string parts[];
   int np = StringSplit(InpExtraDates, ',', parts);
   for(int i = 0; i < np; i++)
   {
      StringTrimLeft(parts[i]); StringTrimRight(parts[i]);
      if(StringLen(parts[i]) < 8) continue;
      int k = ArraySize(g_skip);
      ArrayResize(g_skip, k + 1);
      g_skip[k] = DayOf(StringToTime(parts[i]));
   }

   ArrayResize(g_fomcDays, ArraySize(FOMC_DATES));
   for(int f = 0; f < ArraySize(FOMC_DATES); f++) g_fomcDays[f] = DayOf(StringToTime(FOMC_DATES[f]));
   if(InpNewsExitMinBefore < 3) { Print("ERROR: InpNewsExitMinBefore debe ser 3 o mas"); return INIT_PARAMETERS_INCORRECT; }
   if(MQLInfoInteger(MQL_TESTER)) FileDelete("ORB_AGR_v018_backtest.csv", FILE_COMMON);   // cada test empieza limpio

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   trade.SetTypeFillingBySymbol(_Symbol);

   if(InpAccountSize <= 0) { Print("ERROR: indica el Tamano nominal del challenge (p. ej. 10000)"); return INIT_PARAMETERS_INCORRECT; }
   if(InpStage < 0 || InpStage > 2) { Print("ERROR: Fase debe ser 0, 1 o 2"); return INIT_PARAMETERS_INCORRECT; }
   if(InpModel != 1 && InpModel != 2) { Print("ERROR: Tipo de challenge debe ser 1 (1-Step) o 2 (2-Step)"); return INIT_PARAMETERS_INCORRECT; }
   if(InpModel == 1 && InpStage == 1) { Print("ERROR: el 1-Step no tiene Fase 2. Usa 0 (challenge) o 2 (fondeada)"); return INIT_PARAMETERS_INCORRECT; }
   g_firmDaily = (InpModel == 1) ? InpFirmDaily1StepPct : InpFirmDailyLossPct;
   g_size  = InpAccountSize;
   g_stage = InpStage;
   // en el tester la fase empieza en el deposito; en demo/real en el tamano nominal de la cuenta
   g_base  = MQLInfoInteger(MQL_TESTER) ? AccountInfoDouble(ACCOUNT_BALANCE) : g_size;
   if(AutoSim()) { sim_bought = 1; sim_fees = InpSimFee; if(g_stage == 2) { g_lastPayoutDay = DayOf(TimeCurrent()); g_refundPending = true; } }
   if(!MQLInfoInteger(MQL_TESTER)) g_tradeDays = CountTradingDays();
   g_peak = g_base; ResetDayStats();
   if(OneStep() && !MQLInfoInteger(MQL_TESTER)) RebuildFromHistory();
   g_curDay = DayOf(TimeCurrent());
   g_dayStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_minEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_curRiskPct = StageRisk();
   UpdateRiskState();
   PrintFormat("ORB AGR v0.17: modelo FTMO %s | %s | base %.2f | limite diario %.1f%% | suelo perdida maxima %.2f | dias de trading ya hechos: %d | simulador: %s",
               OneStep() ? "1-Step" : "2-Step", StageName(), g_base, g_firmDaily, FloorTotal(), g_tradeDays, AutoSim() ? "SI" : "no");
   PrintFormat("ORB v0.16: riesgo vigente %.2f%% | PF movil %.2f sobre %d operaciones | detenido: %s",
               g_curRiskPct, g_pf, g_pfTrades, g_pfHalt ? "SI" : "no");

   Print("*** BUILD 13/10/2026-I: riesgo challenge 1.8% | cuenta agotada = perdida (InpExhaustPct) | avisos push al movil + FOMC y festivos 2027 | trailing en el challenge + stop a entrada en la fondeada | modo FTMO 1-Step (trailing, diaria 3%, Best Day Rule) o 2-Step, riesgo reducido tras objetivo en vez de lote minimo, cierre FOMC, filtro de noticias desactivado ***");
   PrintFormat("ORB init: cuenta %.0f | riesgo/trade %.2f%% = %.2f | rango %d min | modo entrada %d | stop modo %d | objetivo %.1fR | dias bloqueados %d",
               g_size, StageRisk(), g_size * StageRisk() / 100.0, InpORMinutes, InpEntryMode, InpStopMode, InpTargetR, ArraySize(g_skip));
   Push(StringFormat("EA arrancado (BUILD I) | %s | balance %.2f | suelo %.2f", StageName(), AccountInfoDouble(ACCOUNT_BALANCE), FloorTotal()));
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void FinalizeDayStats()
{
   g_days++;
   if(g_dayWorstDD > g_worstDailyDD) g_worstDailyDD = g_dayWorstDD;
   if(g_dayWorstDD >= InpFirmDailyLossPct) g_breachDays++;
}

void OnDeinit(const int reason)
{
   FinalizeDayStats();
   double maxTotalDD = (g_size - g_minEquity) / g_size * 100.0;
   PrintFormat("=== RESUMEN REGLAS FIRMA === dias: %d | peor dia: %.2f%% | dias que rompen %.1f%%: %d | peor DD total vs cuenta: %.2f%%",
               g_days, g_worstDailyDD, InpFirmDailyLossPct, g_breachDays, MathMax(0.0, maxTotalDD));
   PrintFormat("=== DIAGNOSTICO ORB === dias evaluados: %d | bloqueados: %d | rango ok: %d | fuera tamano: %d | doji: %d | lado no permitido: %d | contra tendencia: %d | noticias: %d | spread: %d | lote < minimo: %d | ordenes: %d | ejecutadas: %d | cerradas dia siguiente: %d | fallos de cierre: %d",
               d_days, d_skip, d_range, d_size, d_doji, d_side, d_trend, d_news, d_spread, d_lots, d_orders, d_fills, d_overnight, d_closefail);
   PrintFormat("=== CONTROL v0.16 === PF movil final: %.2f (%d ops) | dias con riesgo reducido: %d | detenido por PF: %s | cierres antes de noticias/FOMC: %d | entradas tardias descartadas: %d",
               g_pf, g_pfTrades, d_pfreduced, g_pfHalt ? "SI" : "no", d_newsexit, d_late);
   PrintFormat("=== TRAILING (BUILD G) === challenge: %s (activa %.1f R, distancia %.1f R) | stop a entrada fondeada: %.1f R | modificaciones de trailing: %d | stops a entrada: %d | cuentas agotadas: %d",
               InpTrailChallenge ? "SI" : "no", InpTrailActR, InpTrailDistR, InpFundedBreakevenR, d_trailMods, d_beMods, d_exhausted);
   if(AutoSim())
      PrintFormat("=== SIMULADOR CHALLENGES === cuotas: %d (%.0f $) | fase 1 superadas: %d | fase 2 superadas: %d | fallos: %d | retiros: %d por %.2f $ | NETO: %.2f $ | primera fondeada: %s | primer retiro: %s | fase final: %s",
                  sim_bought, sim_fees, sim_p1, sim_p2, sim_fail, sim_payN, sim_paySum, sim_paySum - sim_fees,
                  (sim_firstFunded > 0) ? TimeToString(sim_firstFunded, TIME_DATE) : "-", (sim_firstPay > 0) ? TimeToString(sim_firstPay, TIME_DATE) : "-", StageName());
   IndicatorRelease(hAtrD);
   IndicatorRelease(hEma);
}

//+------------------------------------------------------------------+
bool IsSkipDay()
{
   for(int i = 0; i < ArraySize(g_skip); i++)
      if(g_skip[i] == g_curDay) return true;
   return false;
}

bool IsOurPosition()
{
   return PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic;
}

bool HasPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0 && IsOurPosition()) return true;
   return false;
}

// Orden seleccionada = pendiente de verdad (stop/limit), no la orden a mercado que MT5 crea al cerrar
bool IsPendingType()
{
   long ot = OrderGetInteger(ORDER_TYPE);
   return ot != ORDER_TYPE_BUY && ot != ORDER_TYPE_SELL && ot != ORDER_TYPE_CLOSE_BY;
}

int CountPending()
{
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t > 0 && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == InpMagic && IsPendingType()) n++;
   }
   return n;
}

void DeletePending()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t > 0 && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == InpMagic && IsPendingType())
         trade.OrderDelete(t);
   }
}

void CloseAll(string why)
{
   DeletePending();
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t > 0 && IsOurPosition())
      {
         bool ok = trade.PositionClose(t);
         if(!ok)
         {
            // reintento con otros modos de ejecucion
            ENUM_ORDER_TYPE_FILLING modes[3] = {ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN};
            for(int m = 0; m < 3 && !ok; m++)
            {
               trade.SetTypeFilling(modes[m]);
               ok = trade.PositionClose(t);
            }
            trade.SetTypeFillingBySymbol(_Symbol);
         }
         if(ok) Print("Cierre (", why, ") ticket ", t);
         else
         {
            d_closefail++;
            if(d_closefail <= 30) PrintFormat("FALLO al cerrar ticket %I64u (%s): retcode %u %s", t, why, trade.ResultRetcode(), trade.ResultRetcodeDescription());
         }
      }
   }
}

void UpdateDay(datetime now)
{
   datetime d = DayOf(now);
   if(d == g_curDay) return;
   FinalizeDayStats();
   DeletePending();                       // nunca arrastrar ordenes al dia siguiente
   g_curDay = d;
   g_dayStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(OneStep())
   {
      // demo/real: se reconstruye cada dia desde el historial (detecta retiros, que reinician el trailing)
      if(!MQLInfoInteger(MQL_TESTER)) RebuildFromHistory();
      g_peak = MathMax(g_peak, g_dayStartBalance);   // trailing sobre el balance de cierre de dia
      if(!MQLInfoInteger(MQL_TESTER))
      {
         double best, pos; bool ok = BestDayOk(best, pos);
         PrintFormat("1-Step %s: balance %.2f | suelo perdida maxima %.2f | Best Day %.2f de %.2f -> %s",
                     StageName(), g_dayStartBalance, FloorTotal(), best, pos, ok ? "cumple" : "no cumple todavia");
      }
   }
   g_tradesToday = 0;
   g_dayLocked = false;
   g_dayWorstDD = 0;
   g_rangeDone = false;
   g_beDone = false;
   g_riskDist = 0;
   g_mfe = 0; g_mfeTicket = 0;
   UpdateRiskState();
   if(g_curRiskPct < StageRisk()) d_pfreduced++;
}

//+------------------------------------------------------------------+
// Ya hubo una entrada de este EA hoy (aunque se haya cerrado a mano o el EA se haya reiniciado)
bool TradedToday()
{
   if(!HistorySelect(g_curDay, TimeCurrent() + 60)) return false;
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0) continue;
      if(HistoryDealGetInteger(d, DEAL_MAGIC) != InpMagic) continue;
      if(HistoryDealGetString(d, DEAL_SYMBOL) != _Symbol) continue;
      if(HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN) return true;
   }
   return false;
}

// Noticia USD de alto impacto relevante para el Nasdaq entre 'from' y 'to' (hora del servidor).
// Ignora las que contienen alguno de los textos de InpNewsExclude (petroleo, gas, discursos de miembros de la Fed...).
bool HighNewsBetween(datetime from, datetime to, string &evName, datetime &evTime)
{
   MqlCalendarValue vals[];
   int n = CalendarValueHistory(vals, from, to, NULL, "USD");
   string excl[];
   int ne = StringSplit(InpNewsExclude, ';', excl);
   for(int i = 0; i < n; i++)
   {
      MqlCalendarEvent ev;
      if(!CalendarEventById(vals[i].event_id, ev) || ev.importance != CALENDAR_IMPORTANCE_HIGH) continue;
      string nm = ev.name;
      string up = nm; StringToUpper(up);
      bool skip = false;
      for(int k = 0; k < ne && !skip; k++)
      {
         string w = excl[k]; StringTrimLeft(w); StringTrimRight(w); StringToUpper(w);
         if(StringLen(w) > 0 && StringFind(up, w) >= 0) skip = true;
      }
      if(skip) continue;
      evName = nm; evTime = vals[i].time;
      return true;
   }
   return false;
}

bool NewsBlocked(datetime now)
{
   if(!InpNewsFilter || MQLInfoInteger(MQL_TESTER)) return false;
   datetime sessStart = AtHHMM(g_curDay, InpSessionStart);
   datetime from = sessStart - InpNewsPreSessionMin * 60;
   datetime entryT = sessStart + InpORMinutes * 60;
   if(now > entryT) entryT = now;
   datetime to   = entryT + InpNewsPostEntryMin * 60;
   string nm; datetime t;
   if(HighNewsBetween(from, to, nm, t))
   {
      PrintFormat("ORB: hoy no opera: noticia USD de alto impacto '%s' a las %s (servidor), dentro de la ventana %s-%s.",
                  nm, TimeToString(t, TIME_MINUTES), TimeToString(from, TIME_MINUTES), TimeToString(to, TIME_MINUTES));
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
bool IsFomcDay()
{
   for(int i = 0; i < ArraySize(g_fomcDays); i++)
      if(g_fomcDays[i] == g_curDay) return true;
   return false;
}

// PF de las ultimas InpPfWindow operaciones cerradas de este EA -> riesgo vigente
void UpdateRiskState()
{
   g_curRiskPct = StageRisk();
   if(!InpPfControl) return;
   if(!HistorySelect(0, TimeCurrent() + 60)) return;
   double gp = 0, gl = 0;
   int n = 0;
   for(int i = HistoryDealsTotal() - 1; i >= 0 && n < InpPfWindow; i--)
   {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0) continue;
      if(HistoryDealGetInteger(d, DEAL_MAGIC) != InpMagic) continue;
      if(HistoryDealGetString(d, DEAL_SYMBOL) != _Symbol) continue;
      long e = HistoryDealGetInteger(d, DEAL_ENTRY);
      double c = HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_FEE);
      if(MQLInfoInteger(MQL_TESTER) && !InpCommInTester) c = 0;
      if(e == DEAL_ENTRY_IN) { if(c < 0) gl -= c; continue; }
      if(e != DEAL_ENTRY_OUT && e != DEAL_ENTRY_OUT_BY) continue;
      double p = HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_SWAP) + c;
      if(p >= 0) gp += p; else gl -= p;
      n++;
   }
   g_pfTrades = n;
   g_pf = (gl > 0) ? gp / gl : ((gp > 0) ? 99.0 : 0.0);
   if(n < InpPfMinTrades) return;
   if(g_pf < InpPfHaltBelow)
   {
      if(!g_pfHalt)
      {
         PrintFormat("PF movil %.2f (%d ops) por debajo de %.2f: EA DETENIDO. Revisar la estrategia antes de reactivar.", g_pf, n, InpPfHaltBelow);
         d_pfhalt++;
      }
      g_pfHalt = true;
   }
   if(g_pf < InpPfReduceBelow) g_curRiskPct = MathMin(StageRisk(), InpRiskReducedPct);
}

double RiskMoney(double lots, double slDist)
{
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0) tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize <= 0) return 0;
   return lots * slDist / tickSize * tickValue;
}

// Cierra la posicion antes de noticias USD de alto impacto y del FOMC.
// Nunca cierra dentro de los 150 s previos al dato (ventana prohibida de FTMO): en ese caso aguanta.
void NewsExitCheck(datetime now)
{
   if(!HasPosition()) return;
   // El cierre del FOMC va primero y no depende de InpNewsExit
   if(InpFomcClose && IsFomcDay())
   {
      datetime fomc = AtHHMM(g_curDay, InpFomcServerHHMM);
      if(now >= fomc - InpNewsExitMinBefore * 60 && now < fomc - 150)
      { d_newsexit++; CloseAll("antes del FOMC"); return; }
   }
   if(!InpNewsExit || MQLInfoInteger(MQL_TESTER)) return;
   static datetime lastCheck = 0;
   if(now - lastCheck < 20) return;
   lastCheck = now;
   string nm; datetime t;
   if(HighNewsBetween(now + 150, now + InpNewsExitMinBefore * 60, nm, t))
   {
      d_newsexit++;
      CloseAll("antes de noticia USD: " + nm + " " + TimeToString(t, TIME_MINUTES));
   }
}

// Dias distintos con alguna entrada en el historial de la cuenta (cuenta dedicada a una fase)
int CountTradingDays()
{
   if(!HistorySelect(0, TimeCurrent() + 60)) return 0;
   datetime last = 0; int n = 0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0 || HistoryDealGetInteger(d, DEAL_ENTRY) != DEAL_ENTRY_IN) continue;
      datetime day = DayOf((datetime)HistoryDealGetInteger(d, DEAL_TIME));
      if(day != last) { n++; last = day; }
   }
   g_lastTradeDay = last;
   return n;
}

bool OneStep() { return InpModel == 1; }

// Referencia de la perdida maxima: estatica (2-Step) o balance mas alto (1-Step)
double LossRef() { return OneStep() ? MathMax(g_peak, g_base) : g_base; }
double FloorTotal() { return LossRef() - InpFirmMaxLossPct / 100.0 * g_size; }
double BrakeTotal() { return LossRef() - InpMaxLossPct / 100.0 * g_size; }
double DailyBrakePct() { return MathMin(InpDailyLossPct, g_firmDaily - 0.5); }

void ResetDayStats() { g_bestDay = 0; g_posDays = 0; g_todayPnl = 0; g_pnlDay = 0; g_bdWarned = false; }
void CommitDay()
{
   if(g_todayPnl > 0) { g_posDays += g_todayPnl; if(g_todayPnl > g_bestDay) g_bestDay = g_todayPnl; }
   g_todayPnl = 0;
}
void AddDayPnl(datetime t, double pnl)
{
   datetime d = DayOf(t);
   if(d != g_pnlDay) { CommitDay(); g_pnlDay = d; }
   g_todayPnl += pnl;
}
// Best Day Rule (incluye el dia en curso)
bool BestDayOk(double &best, double &pos)
{
   best = g_bestDay; pos = g_posDays;
   if(g_todayPnl > 0) { pos += g_todayPnl; best = MathMax(best, g_todayPnl); }
   return pos > 0 && best <= InpBestDayPct / 100.0 * pos;
}

// Demo/real 1-Step: reconstruye el balance mas alto y los dias positivos desde el historial de la cuenta.
// Un retiro (operacion de balance negativa) reinicia el trailing y el ciclo de la Best Day Rule.
void RebuildFromHistory()
{
   if(!HistorySelect(0, TimeCurrent() + 60)) return;
   double running = 0, peak = 0;
   ResetDayStats();
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0) continue;
      long typ = HistoryDealGetInteger(d, DEAL_TYPE);
      double amt = HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION)
                 + HistoryDealGetDouble(d, DEAL_SWAP) + HistoryDealGetDouble(d, DEAL_FEE);
      running += amt;
      if(typ == DEAL_TYPE_BALANCE)
      {
         if(amt < 0) { peak = running; ResetDayStats(); }   // retiro: nuevo ciclo
         else peak = MathMax(peak, running);
         continue;
      }
      long e = HistoryDealGetInteger(d, DEAL_ENTRY);
      if(e == DEAL_ENTRY_OUT || e == DEAL_ENTRY_OUT_BY)
      {
         AddDayPnl((datetime)HistoryDealGetInteger(d, DEAL_TIME), amt);
         peak = MathMax(peak, running);   // mas prudente que el cierre de dia de FTMO
      }
   }
   g_peak = MathMax(peak, g_base);
}

bool AutoSim() { return InpAutoStages && MQLInfoInteger(MQL_TESTER); }

double StageRisk()
{
   if(g_stage == 0) return InpRiskP1Pct;
   if(g_stage == 1) return InpRiskP2Pct;
   return InpRiskFundedPct;
}

string StageName()
{
   if(OneStep()) return (g_stage == 0) ? "Challenge 1-Step" : "Fondeada 1-Step";
   return (g_stage == 0) ? "Fase 1" : (g_stage == 1) ? "Fase 2" : "Fondeada";
}

// Simulador: la cuenta ha fallado -> se "compra" un challenge nuevo
void SimNewChallenge()
{
   g_stage = 0;
   g_base = AccountInfoDouble(ACCOUNT_BALANCE);
   g_dayStartBalance = g_base;            // cuenta nueva: el limite diario parte de aqui
   g_peak = g_base; ResetDayStats();
   g_tradeDays = 0; g_lastTradeDay = 0; g_targetHit = false; g_refundPending = false;
   sim_bought++; sim_fees += InpSimFee;
   UpdateRiskState();
   PrintFormat("SIM %s: compra del challenge n.%d", TimeToString(TimeCurrent(), TIME_DATE), sim_bought);
}

void StageFailed(string why)
{
   CloseAll(why);
   Push(StringFormat("FRENO: %s | equity %.2f. El EA deja de operar en esta cuenta.", why, AccountInfoDouble(ACCOUNT_EQUITY)));
   if(AutoSim())
   {
      sim_fail++;
      PrintFormat("SIM %s: FALLO en %s (%s) | balance fase %.2f", TimeToString(TimeCurrent(), TIME_DATE), StageName(), why,
                  AccountInfoDouble(ACCOUNT_BALANCE) - g_base);
      SimNewChallenge();
   }
   else
   {
      g_totalLocked = true;
      PrintFormat("CUENTA PERDIDA O EN EL LIMITE (%s): el EA no opera mas en esta cuenta.", why);
   }
}

// Objetivos de fase, dias minimos, retiros simulados
void StageCheck()
{
   if(HasPosition()) return;
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   if(g_stage < 2 && OneStep())
   {
      double target1 = InpTargetP1Pct / 100.0 * g_size;
      if(bal - g_base >= target1)
      {
         double best, pos;
         if(BestDayOk(best, pos))
         {
            if(AutoSim())
            {
               sim_p1++; g_stage = 2; g_lastPayoutDay = g_curDay; g_refundPending = false;
               if(sim_firstFunded == 0) sim_firstFunded = TimeCurrent();
               PrintFormat("SIM %s: challenge 1-Step superado -> %s", TimeToString(TimeCurrent(), TIME_DATE), StageName());
               g_base = bal; g_peak = bal; ResetDayStats();
               UpdateRiskState();
            }
            else if(!g_totalLocked)
            {
               g_totalLocked = true;
               PrintFormat("CHALLENGE 1-STEP SUPERADO: +%.2f y Best Day %.2f de %.2f. El EA deja de operar en esta cuenta.", bal - g_base, best, pos);
               Push(StringFormat("CHALLENGE SUPERADO (+%.2f). El EA se detiene. Pon InpStage=2 en la cuenta fondeada.", bal - g_base));
            }
         }
         else if(!g_bdWarned)
         {
            g_bdWarned = true;
            PrintFormat("%s: objetivo alcanzado (+%.2f) pero falta la Best Day Rule: mejor dia %.2f > %.0f%% de %.2f. Sigue operando con normalidad.",
                        TimeToString(TimeCurrent(), TIME_DATE), bal - g_base, best, InpBestDayPct, pos);
            Push(StringFormat("Objetivo alcanzado (+%.2f) pero falta la Best Day Rule (mejor dia %.2f de %.2f). Sigue operando.", bal - g_base, best, pos));
         }
      }
   }
   else if(g_stage < 2)
   {
      double target = ((g_stage == 0) ? InpTargetP1Pct : InpTargetP2Pct) / 100.0 * g_size;
      if(!g_targetHit && bal - g_base >= target)
      {
         g_targetHit = true;
         PrintFormat("%s: objetivo de %s alcanzado (%.2f). Dias de trading: %d de %d", TimeToString(TimeCurrent(), TIME_DATE),
                     StageName(), bal - g_base, g_tradeDays, InpMinTradingDays);
      }
      if(g_targetHit && g_tradeDays >= InpMinTradingDays && bal - g_base >= target)
      {
         if(AutoSim())
         {
            if(g_stage == 0) { sim_p1++; g_stage = 1; }
            else
            {
               sim_p2++; g_stage = 2; g_lastPayoutDay = g_curDay; g_refundPending = true;
               if(sim_firstFunded == 0) sim_firstFunded = TimeCurrent();
            }
            PrintFormat("SIM %s: fase superada -> %s", TimeToString(TimeCurrent(), TIME_DATE), StageName());
            g_base = bal; g_tradeDays = 0; g_lastTradeDay = 0; g_targetHit = false;
            UpdateRiskState();
         }
         else if(!g_totalLocked)
         {
            g_totalLocked = true;
            PrintFormat("FASE SUPERADA (%s): objetivo y dias minimos cumplidos. El EA deja de operar en esta cuenta.", StageName());
            Push(StringFormat("FASE SUPERADA (%s). El EA se detiene.", StageName()));
         }
      }
   }
   else if(AutoSim() && g_stage == 2 && g_curDay - g_lastPayoutDay >= InpPayoutDays * 86400 && bal - g_base > 0
           && (!OneStep() || BestDayOk(g_bdTmp1, g_bdTmp2)))
   {
      double split = OneStep() ? InpPayoutSplit1Step : InpPayoutSplit;
      double pay = (bal - g_base) * split / 100.0 + (g_refundPending ? InpSimFee : 0);
      sim_payN++; sim_paySum += pay; g_refundPending = false;
      if(sim_firstPay == 0) sim_firstPay = TimeCurrent();
      PrintFormat("SIM %s: RETIRO n.%d de %.2f $ | acumulado %.2f $ | cuotas pagadas %.2f $",
                  TimeToString(TimeCurrent(), TIME_DATE), sim_payN, pay, sim_paySum, sim_fees);
      g_base = bal; g_lastPayoutDay = g_curDay; g_peak = bal; ResetDayStats();
   }
}

double CalcLots(double slDist, double price)
{
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0) tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize <= 0 || tickValue <= 0 || slDist <= 0) return 0;

   // 2-Step con objetivo cumplido y dias minimos pendientes: riesgo reducido pero proporcionado (no lote minimo)
   double riskPct = g_targetHit ? MathMin(g_curRiskPct, InpRiskAfterTargetPct) : g_curRiskPct;
   // challenge cerca del objetivo: riesgo reducido (estudio 09/10/2026: ahorra cuotas, +50 $/ano)
   if(g_stage < 2 && InpNearTargetPct > 0 && AccountInfoDouble(ACCOUNT_BALANCE) - g_base >= InpNearTargetPct / 100.0 * g_size)
      riskPct = MathMin(riskPct, InpNearTargetRiskPct);

   // riesgo de la fase, recortado por el colchon frente a los limites reales de la firma
   double eqNow = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = g_size * riskPct / 100.0;
   double cushTotal = eqNow - FloorTotal() - InpCushionPct / 100.0 * g_size;
   // cuenta agotada: el margen hasta el suelo no da ni para la mitad del riesgo normal -> recuperar el objetivo es casi imposible
   g_exhausted = (InpExhaustPct > 0 && cushTotal < InpExhaustPct / 100.0 * riskMoney);
   if(g_exhausted) return 0;
   double cushDay   = eqNow - (g_dayStartBalance - g_firmDaily / 100.0 * g_size) - InpCushionPct / 100.0 * g_size;
   riskMoney = MathMin(riskMoney, MathMin(cushTotal, cushDay));
   if(riskMoney <= 0) return 0;

   double lots = riskMoney / (slDist / tickSize * tickValue);

   // tope de exposicion: nocional por lote = precio * valor de 1 punto por lote
   if(InpMaxNotionalX > 0 && price > 0)
   {
      double notionalPerLot = price / tickSize * tickValue;
      double capLots = g_size * InpMaxNotionalX / notionalPerLot;
      if(lots > capLots) lots = capLots;
   }

   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step > 0) lots = MathFloor(lots / step) * step;
   if(lots < vmin) return 0;
   if(lots > vmax) lots = vmax;
   return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
// v0.18: percentil del ATR(14) diario en % del precio (barra de ayer) frente a los ultimos InpVolLookback dias
int d_vol = 0;
bool VolTooHigh(double &pct)
{
   int n = InpVolLookback + 1;
   double a[], c[];
   ArraySetAsSeries(a, true); ArraySetAsSeries(c, true);
   if(CopyBuffer(hAtrD, 0, 1, n, a) != n) return false;           // sin historico suficiente: no filtra
   if(CopyClose(_Symbol, PERIOD_D1, 1, n, c) != n) return false;
   if(c[0] <= 0) return false;
   double cur = a[0] / c[0]; int below = 0, cnt = 0;
   for(int i = 1; i < n; i++) { if(c[i] <= 0) continue; cnt++; if(a[i] / c[i] < cur) below++; }
   if(cnt < 120) return false;
   pct = 100.0 * below / cnt;
   return pct > InpVolPct;
}

//+------------------------------------------------------------------+
// Evalua el rango de apertura una sola vez al dia, cuando ha terminado
void EvaluateRange(datetime now)
{
   datetime sessStart = AtHHMM(g_curDay, InpSessionStart);
   datetime rangeEnd  = sessStart + InpORMinutes * 60;
   if(now < rangeEnd) return;
   g_rangeDone = true;
   d_days++;

   if(IsSkipDay()) { d_skip++; Print("ORB: hoy no opera: festivo o cierre anticipado de la bolsa USA."); return; }
   if(now > rangeEnd + InpMaxEntryDelayMin * 60)
   {
      d_late++;
      PrintFormat("ORB: rango terminado a las %s y ahora son las %s: entrada tardia descartada (no seria la misma operacion del backtest).",
                  TimeToString(rangeEnd, TIME_MINUTES), TimeToString(now, TIME_MINUTES));
      return;
   }
   if(now > AtHHMM(g_curDay, InpTradeEnd)) return;
   if(HasPosition() || TradedToday())
   {
      Print("ORB: ya hubo una operacion de este EA hoy: no se repite la entrada.");
      return;
   }

   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, sessStart, rangeEnd - 60, r);
   if(n <= 0) return;
   // exigir que la primera vela sea realmente la de apertura (evita festivos/huecos)
   if(r[0].time > sessStart + 120) { Print("ORB: hoy no opera: no hay datos de la apertura (primera vela a las ", TimeToString(r[0].time, TIME_MINUTES), ")."); return; }

   double hi = r[0].high, lo = r[0].low, op = r[0].open, cl = r[n - 1].close;
   for(int i = 1; i < n; i++) { hi = MathMax(hi, r[i].high); lo = MathMin(lo, r[i].low); }
   double range = hi - lo;
   if(range <= 0) return;
   d_range++;

   double atrD[];
   if(CopyBuffer(hAtrD, 0, 1, 1, atrD) != 1 || atrD[0] <= 0) return;
   if(InpMinRangeAtrPct > 0 && range < atrD[0] * InpMinRangeAtrPct / 100.0) { d_size++; Print("ORB: hoy no opera: rango demasiado pequeno."); return; }
   if(InpMaxRangeAtrPct > 0 && range > atrD[0] * InpMaxRangeAtrPct / 100.0) { d_size++; Print("ORB: hoy no opera: rango demasiado grande."); return; }
   if(InpVolFilter)
   {
      double vp = 0;
      if(VolTooHigh(vp)) { d_vol++; PrintFormat("ORB: hoy no opera: volatilidad extrema (ATR%% diario en el percentil %.0f, limite %.0f).", vp, InpVolPct); return; }
   }

   if(NewsBlocked(now)) { d_news++; return; }
   if(InpMaxSpreadPoints > 0 && SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPoints) { d_spread++; Print("ORB: hoy no opera: spread demasiado alto."); return; }

   double ema[];
   bool haveEma = (CopyBuffer(hEma, 0, 1, 1, ema) == 1);
   double stopsLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;

   if(InpEntryMode == 0)
   {
      // ---------- direccion de la vela del rango, entrada a mercado ----------
      double body = cl - op;
      if(MathAbs(body) < range * InpMinBodyPct / 100.0)
      {
         d_doji++;
         PrintFormat("ORB: hoy no opera: vela del rango sin cuerpo (cuerpo %.1f de %.1f puntos de rango).", MathAbs(body), range);
         return;
      }
      int dir = (body > 0) ? 1 : -1;
      if((dir == 1 && !InpAllowLong) || (dir == -1 && !InpAllowShort)) { d_side++; Print("ORB: hoy no opera: lado no permitido."); return; }
      double px = (dir == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
      if(InpTrendFilter && haveEma && ((dir == 1 && px < ema[0]) || (dir == -1 && px > ema[0]))) { d_trend++; Print("ORB: hoy no opera: contra la tendencia (EMA H1)."); return; }

      double slDist = (InpStopMode == 0) ? ((dir == 1) ? px - lo : hi - px)
                                         : atrD[0] * InpStopDailyAtrPct / 100.0;
      if(slDist <= stopsLevel || slDist <= 0) return;
      double sl = RoundToTick(px - dir * slDist);
      double tp = (InpTargetR > 0) ? RoundToTick(px + dir * InpTargetR * slDist) : 0;
      double lots = CalcLots(slDist, px);
      if(lots <= 0 && g_exhausted)
      {
         g_exhausted = false; d_exhausted++;
         StageFailed(StringFormat("CUENTA AGOTADA: margen hasta el suelo %.2f, menor que el %.0f%% del riesgo normal. Compra otro challenge",
                                  AccountInfoDouble(ACCOUNT_EQUITY) - FloorTotal(), InpExhaustPct));
         return;
      }
      if(lots <= 0) { d_lots++; Print("ORB: hoy no opera: lote calculado por debajo del minimo."); return; }

      d_orders++;
      g_expEntry = px;
      g_tradeRiskPct = g_curRiskPct;
      g_tradeRiskMoney = RiskMoney(lots, slDist);
      bool ok = (dir == 1) ? trade.Buy(lots, _Symbol, 0, sl, tp, "ORB_L")
                           : trade.Sell(lots, _Symbol, 0, sl, tp, "ORB_S");
      if(ok && trade.ResultRetcode() == TRADE_RETCODE_DONE) { g_tradesToday++; d_fills++; g_riskDist = slDist; }
   }
   else
   {
      // ---------- ruptura clasica: buy stop / sell stop OCO ----------
      double buf = InpBreakBufferPts * _Point;
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

      if(InpAllowLong && !(InpTrendFilter && haveEma && ask < ema[0]))
      {
         double entry = RoundToTick(hi + buf);
         double slDist = (InpStopMode == 0) ? entry - lo : atrD[0] * InpStopDailyAtrPct / 100.0;
         if(entry > ask + stopsLevel && slDist > stopsLevel)
         {
            double lots = CalcLots(slDist, entry);
            double tp = (InpTargetR > 0) ? RoundToTick(entry + InpTargetR * slDist) : 0;
            if(lots > 0 && trade.BuyStop(lots, entry, _Symbol, RoundToTick(entry - slDist), tp, ORDER_TIME_GTC, 0, "ORB_BS"))
            { d_orders++; g_riskDist = slDist; g_tradeRiskPct = g_curRiskPct; g_tradeRiskMoney = RiskMoney(lots, slDist); }
         }
      }
      else d_trend++;

      if(InpAllowShort && !(InpTrendFilter && haveEma && bid > ema[0]))
      {
         double entry = RoundToTick(lo - buf);
         double slDist = (InpStopMode == 0) ? hi - entry : atrD[0] * InpStopDailyAtrPct / 100.0;
         if(entry < bid - stopsLevel && slDist > stopsLevel)
         {
            double lots = CalcLots(slDist, entry);
            double tp = (InpTargetR > 0) ? RoundToTick(entry - InpTargetR * slDist) : 0;
            if(lots > 0 && trade.SellStop(lots, entry, _Symbol, RoundToTick(entry + slDist), tp, ORDER_TIME_GTC, 0, "ORB_SS"))
            { d_orders++; g_riskDist = slDist; g_tradeRiskPct = g_curRiskPct; g_tradeRiskMoney = RiskMoney(lots, slDist); }
         }
      }
      else d_trend++;
   }
}

//+------------------------------------------------------------------+
void Push(string msg)
{
   if(!InpPush || MQLInfoInteger(MQL_TESTER) || MQLInfoInteger(MQL_OPTIMIZATION)) return;
   if(!TerminalInfoInteger(TERMINAL_NOTIFICATIONS_ENABLED)) return;
   if(!SendNotification(StringSubstr("ORB AGR " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ": " + msg, 0, 255)))
      Print("Aviso: no se pudo enviar la notificacion push (error ", GetLastError(), ")");
}

double TradeRiskDist()
{
   if(g_riskDist > 0) return g_riskDist;
   if(InpStopMode != 1) return 0;
   double atrD[];
   if(CopyBuffer(hAtrD, 0, 1, 1, atrD) != 1 || atrD[0] <= 0) return 0;
   g_riskDist = atrD[0] * InpStopDailyAtrPct / 100.0;   // mismo calculo que en la entrada (ATR del dia anterior)
   return g_riskDist;
}

// maximo favorable desde la apertura (tras un reinicio se reconstruye con velas M1)
double UpdateMfe(ulong t, long type, double open, datetime openTime, double px)
{
   double gain = (type == POSITION_TYPE_BUY) ? px - open : open - px;
   if(g_mfeTicket != t)
   {
      g_mfeTicket = t; g_mfe = 0;
      int n = Bars(_Symbol, PERIOD_M1, openTime, TimeCurrent());
      if(n > 1)
      {
         double hh[], ll[];
         if(CopyHigh(_Symbol, PERIOD_M1, openTime, TimeCurrent(), hh) > 0 && CopyLow(_Symbol, PERIOD_M1, openTime, TimeCurrent(), ll) > 0)
         {
            // la vela de la apertura y la actual se excluyen (puede haber precios anteriores a la entrada)
            for(int i = 1; i < ArraySize(hh) - 1; i++)
            {
               double g = (type == POSITION_TYPE_BUY) ? hh[i] - open : open - ll[i];
               if(g > g_mfe) g_mfe = g;
            }
         }
      }
   }
   if(gain > g_mfe) g_mfe = gain;
   return g_mfe;
}

void ManageBreakeven()
{
   bool funded = (g_stage == 2);
   double beR = funded ? MathMax(InpBreakevenR, InpFundedBreakevenR) : InpBreakevenR;
   bool trail = (funded ? InpTrailFunded : InpTrailChallenge) && InpTrailActR > 0 && InpTrailDistR > 0;
   if(beR <= 0 && !trail) return;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0 || !IsOurPosition()) continue;
      double R = TradeRiskDist();
      if(R <= 0) return;
      double open = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl   = PositionGetDouble(POSITION_SL);
      double tp   = PositionGetDouble(POSITION_TP);
      long   type = PositionGetInteger(POSITION_TYPE);
      bool   buy  = (type == POSITION_TYPE_BUY);
      double px   = buy ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double mfe  = UpdateMfe(t, type, open, (datetime)PositionGetInteger(POSITION_TIME), px);

      double target = 0; bool want = false; bool isTrail = false;
      if(beR > 0 && mfe >= beR * R) { target = open; want = true; }
      if(trail && mfe >= InpTrailActR * R)
      {
         double lvl = buy ? open + (mfe - InpTrailDistR * R) : open - (mfe - InpTrailDistR * R);
         if(!want || (buy ? lvl > target : lvl < target)) { target = lvl; want = true; isTrail = true; }
      }
      if(!want) continue;
      double newSl = RoundToTick(target);
      double step  = isTrail ? InpTrailStepR * R : 0;
      bool better = buy ? (sl == 0 || newSl > sl + step) : (sl == 0 || newSl < sl - step);
      if(!better) continue;
      // el stop debe quedar al otro lado del precio y respetar la distancia minima del broker
      double minDist = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
      if(buy ? newSl > px - minDist : newSl < px + minDist) continue;
      if(trade.PositionModify(t, newSl, tp))
      {
         if(isTrail) d_trailMods++; else { d_beMods++; g_beDone = true; }
      }
   }
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime now = TimeCurrent();
   UpdateDay(now);

   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq < g_minEquity) g_minEquity = eq;
   double dd = (g_dayStartBalance - eq) / g_size * 100.0;
   if(dd > g_dayWorstDD) g_dayWorstDD = dd;

   // --- frenos ---
   if(!g_dayLocked && eq <= g_dayStartBalance - DailyBrakePct() / 100.0 * g_size)
   { CloseAll("freno perdida diaria"); g_dayLocked = true; }
   if(!g_totalLocked && eq <= BrakeTotal())
      StageFailed("freno perdida total");
   else if(!g_totalLocked && eq <= g_dayStartBalance - g_firmDaily / 100.0 * g_size)
      StageFailed("limite diario de la firma");
   if(!g_dayLocked && InpDailyProfitCapPct > 0 && eq >= g_dayStartBalance + InpDailyProfitCapPct / 100.0 * g_size)
   { CloseAll("tope beneficio diario"); g_dayLocked = true; }
   if(!g_totalLocked && InpStopAtTargetPct > 0 && eq >= g_base + InpStopAtTargetPct / 100.0 * g_size)
   { CloseAll("objetivo challenge alcanzado"); g_totalLocked = true; }

   int hm = HHMM(now);
   if(hm >= InpFlatTime && (HasPosition() || CountPending() > 0)) CloseAll("hora de cierre");
   if(hm >= InpTradeEnd && CountPending() > 0) DeletePending();

   // OCO: si una orden stop se ejecuto, anular la otra
   if(HasPosition() && CountPending() > 0) DeletePending();

   // seguridad: ninguna posicion debe sobrevivir al dia en que se abrio
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t > 0 && IsOurPosition() && DayOf((datetime)PositionGetInteger(POSITION_TIME)) < g_curDay)
      {
         static datetime lastFlag = 0;
         if(lastFlag != g_curDay) { d_overnight++; lastFlag = g_curDay; }
         CloseAll("posicion de un dia anterior");
         break;
      }
   }

   ManageBreakeven();
   // aviso diario a las 16:45 servidor si no hay operacion (si no llega ningun aviso, el PC o MT5 no estan funcionando)
   static datetime hbDay = 0;
   if(hm >= InpSessionStart + 15 && hbDay != g_curDay)
   {
      hbDay = g_curDay;
      if(!HasPosition() && g_tradesToday == 0 && !g_totalLocked)
         Push(StringFormat("Hoy no opera (motivo en Expertos) | balance %.2f | suelo %.2f", AccountInfoDouble(ACCOUNT_BALANCE), FloorTotal()));
   }
   NewsExitCheck(now);
   if(!g_totalLocked) StageCheck();

   if(g_dayLocked || g_totalLocked || g_pfHalt) return;
   if(g_rangeDone || g_tradesToday >= InpMaxTradesDay) return;
   if(hm < InpSessionStart) return;

   EvaluateRange(now);
}

//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;
   long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   long dtype = HistoryDealGetInteger(trans.deal, DEAL_TYPE);

   // ---------- entrada: guardar precio, slippage y comision ----------
   if(entry == DEAL_ENTRY_IN)
   {
      if(InpEntryMode == 1) { g_tradesToday++; d_fills++; }
      double fill = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
      double expPx = g_expEntry;
      if(InpEntryMode == 1)
      {
         ulong ord = (ulong)HistoryDealGetInteger(trans.deal, DEAL_ORDER);
         if(HistoryOrderSelect(ord)) expPx = HistoryOrderGetDouble(ord, ORDER_PRICE_OPEN);
      }
      datetime inDay = DayOf((datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME));
      if(inDay != g_lastTradeDay) { g_tradeDays++; g_lastTradeDay = inDay; }
      g_inPrice   = fill;
      g_inSlipPts = (expPx > 0) ? ((dtype == DEAL_TYPE_BUY) ? fill - expPx : expPx - fill) / _Point : 0;   // positivo = en contra
      g_inComm    = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) + HistoryDealGetDouble(trans.deal, DEAL_FEE);
      double tsz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE), tvl = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double rMoney = (tsz > 0) ? HistoryDealGetDouble(trans.deal, DEAL_VOLUME) * g_riskDist / tsz * tvl : 0;
      Push(StringFormat("Entrada %s %.2f lotes a %.2f | riesgo %.0f $ (%s)", (dtype == DEAL_TYPE_BUY) ? "COMPRA" : "VENTA",
                        HistoryDealGetDouble(trans.deal, DEAL_VOLUME), fill, rMoney, StageName()));
      return;
   }
   if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY) return;

   // ---------- salida ----------
   double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);
   double comm   = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) + HistoryDealGetDouble(trans.deal, DEAL_FEE);
   double swap   = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
   double commTotal = comm + g_inComm;
   bool   useComm = !(MQLInfoInteger(MQL_TESTER) && !InpCommInTester);
   double net    = profit + swap + (useComm ? commTotal : 0);   // en el tester de FTMO se ignora la comision irreal
   double outPx  = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double dsl    = HistoryDealGetDouble(trans.deal, DEAL_SL);
   double vol    = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
   string side   = (dtype == DEAL_TYPE_SELL) ? "LONG" : "SHORT";
   long   reason = HistoryDealGetInteger(trans.deal, DEAL_REASON);
   string why    = (reason == DEAL_REASON_SL) ? "SL" : (reason == DEAL_REASON_TP) ? "TP" : "EA";
   Push(StringFormat("Salida %s (%s) a %.2f: %+.2f $ | balance %.2f", side, why, outPx, net, AccountInfoDouble(ACCOUNT_BALANCE)));

   double outSlipPts = 0;
   if(reason == DEAL_REASON_SL && dsl > 0)
      outSlipPts = ((dtype == DEAL_TYPE_SELL) ? dsl - outPx : outPx - dsl) / _Point;   // positivo = en contra
   double stopPts = (g_riskDist > 0) ? g_riskDist / _Point : 0;
   double slipPct = (stopPts > 0) ? (MathMax(0.0, g_inSlipPts) + MathMax(0.0, outSlipPts)) / stopPts * 100.0 : 0;
   double rMult   = (g_tradeRiskMoney > 0) ? net / g_tradeRiskMoney : 0;

   datetime t = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
   AddDayPnl(t, net);
   UpdateRiskState();

   if(InpLogCsv)
   {
      string fname = MQLInfoInteger(MQL_TESTER) ? "ORB_AGR_v018_backtest.csv" : "ORB_AGR_v018_live_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ".csv";   // 14/11/2026: n. de cuenta en el nombre (varias cuentas comparten Common\Files)
      int fh = FileOpen(fname, FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ';');
      if(fh != INVALID_HANDLE)
      {
         if(FileSize(fh) == 0)
            FileWrite(fh, "Fecha", "Hora", "Simbolo", "Lado", "Lotes", "PrecioEntrada", "PrecioSalida", "Salida",
                      "StopPts", "RiesgoPct", "RiesgoDinero", "PnL_bruto", "Comision", "Swap", "PnL_neto", "R",
                      "SlipEntradaPts", "SlipSalidaPts", "SlipPctStop", "PF_movil", "Balance");
         FileSeek(fh, 0, SEEK_END);
         FileWrite(fh, TimeToString(t, TIME_DATE), TimeToString(t, TIME_MINUTES), _Symbol, side,
                   DoubleToString(vol, 2), DoubleToString(g_inPrice, _Digits), DoubleToString(outPx, _Digits), why,
                   DoubleToString(stopPts, 0), DoubleToString(g_tradeRiskPct, 2), DoubleToString(g_tradeRiskMoney, 2),
                   DoubleToString(profit, 2), DoubleToString(commTotal, 2), DoubleToString(swap, 2), DoubleToString(net, 2),
                   DoubleToString(rMult, 3), DoubleToString(g_inSlipPts, 1), DoubleToString(outSlipPts, 1),
                   DoubleToString(slipPct, 2), DoubleToString(g_pf, 3), DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
         FileClose(fh);
      }
   }
   g_inComm = 0; g_inSlipPts = 0; g_expEntry = 0;
}

//+------------------------------------------------------------------+
double OnTester()
{
   if(AutoSim()) return sim_paySum - sim_fees;
   if(g_breachDays > 0 || g_dayWorstDD >= InpFirmDailyLossPct) return 0.0;
   double profit = TesterStatistics(STAT_PROFIT);
   double dd     = TesterStatistics(STAT_EQUITY_DD);
   if(dd <= 0) return profit;
   return profit / dd;
}
//+------------------------------------------------------------------+
