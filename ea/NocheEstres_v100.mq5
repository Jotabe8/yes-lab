//+------------------------------------------------------------------+
//| NocheEstres_v100.mq5                                             |
//| Prima nocturna tras un día de estrés (ver RESULTADOS_NOCHE.md).  |
//| Regla validada en Python 2018-2026 sobre 7 índices:              |
//|   si la sesión cae más de InpCaidaPct desde su apertura, comprar |
//|   al cierre de la sesión y vender poco después de la apertura    |
//|   siguiente. Stop fijo en % del precio. Sin objetivo.            |
//| Hecho sobre metodo/PlantillaPropEA.mq5; solo se han rellenado    |
//| Senal() y Gestionar().                                           |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.00"

#include <Trade/Trade.mqh>

//--- Regla (horas en hora del SERVIDOR, FTMO = EET = CET+1)
input int    InpAperturaHora  = 10;    // Apertura de la sesión (EU 10:00, US 16:30)
input int    InpAperturaMin   = 0;
input int    InpEntradaHora   = 23;    // Cierre de la sesión: momento de la compra
input int    InpEntradaMin    = 0;
input int    InpSalidaHora    = 10;    // Salida al día siguiente (EU 10:10, US 16:35)
input int    InpSalidaMin     = 10;
input double InpCaidaPct      = 1.5;   // Caída mínima de la sesión para entrar (%)
input double InpStopPct       = 1.0;   // Stop en % del precio de entrada
//--- Riesgo
input double InpRiesgoPct        = 0.75;   // Riesgo por operación (% del balance)
input double InpLotesFijos       = 0.0;
//--- Límites de la cuenta
input double InpPerdidaDiariaPct = 4.0;
input double InpPerdidaTotalPct  = 8.0;
input double InpBalanceInicial   = 0.0;
input double InpObjetivoPct      = 0.0;
//--- Filtros
input int    InpMaxOpsDia        = 1;
input double InpMaxSpreadPuntos  = 0;
input long   InpMagic            = 260101;
input bool   InpRegistrarCSV     = true;

CTrade trade;
string g_prefijo;
datetime g_dia = 0;
double g_baseDia = 0;
bool   g_paradoDia = false;
bool   g_paradoTotal = false;
int    g_opsHoy = 0;
double g_inicial = 0;

//+------------------------------------------------------------------+
//| Minutos desde medianoche de una hora de entrada                   |
//+------------------------------------------------------------------+
int Minutos(int hora, int minuto) { return hora * 60 + minuto; }

//+------------------------------------------------------------------+
//| Precio de apertura de la sesión de hoy (primera vela a esa hora)  |
//+------------------------------------------------------------------+
double AperturaSesion()
  {
   datetime ahora = TimeCurrent();
   datetime inicio = ahora - (ahora % 86400) + Minutos(InpAperturaHora, InpAperturaMin) * 60;
   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, inicio, 30, r);   // tolera hasta 30 min sin cotización
   if(n <= 0) return 0;
   return r[0].open;
  }

//+------------------------------------------------------------------+
//| Senal: +1 compra en el minuto de entrada si la sesión ha caído    |
//+------------------------------------------------------------------+
int Senal(double &sl, double &tp)
  {
   sl = 0; tp = 0;
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   int ahora = Minutos(t.hour, t.min), entrada = Minutos(InpEntradaHora, InpEntradaMin);
   if(ahora < entrada || ahora > entrada + 5) return 0;    // ventana de 5 minutos

   double apertura = AperturaSesion();
   if(apertura <= 0) return 0;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(bid <= 0 || ask <= 0) return 0;
   if(bid / apertura - 1.0 > -InpCaidaPct / 100.0) return 0;

   sl = ask * (1.0 - InpStopPct / 100.0);
   return +1;
  }

//+------------------------------------------------------------------+
//| Gestionar: salida por hora al día siguiente                       |
//+------------------------------------------------------------------+
void Gestionar(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket)) return;
   datetime abierta = (datetime)PositionGetInteger(POSITION_TIME);
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   int ahora = Minutos(t.hour, t.min), salida = Minutos(InpSalidaHora, InpSalidaMin);
   bool otroDia = (TimeCurrent() - (TimeCurrent() % 86400)) > (abierta - (abierta % 86400));
   if(otroDia && ahora >= salida)
      CerrarTodo("salida por hora");
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(20);
   g_prefijo = StringFormat("noche_%I64d_%I64d_%s_", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, _Symbol);
   g_inicial = InpBalanceInicial > 0 ? InpBalanceInicial : CargarGV("inicial", AccountInfoDouble(ACCOUNT_BALANCE));
   GuardarGV("inicial", g_inicial);
   g_paradoTotal = CargarGV("parado_total", 0) > 0;
   NuevoDiaSiToca();
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   NuevoDiaSiToca();
   if(!ComprobarLimites()) return;

   ulong ticket = PosicionPropia();
   if(ticket != 0) { Gestionar(ticket); return; }

   if(!VelaNueva()) return;
   if(g_opsHoy >= InpMaxOpsDia) return;
   if(InpMaxSpreadPuntos > 0 && SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPuntos) return;

   double sl, tp;
   int dir = Senal(sl, tp);
   if(dir == 0 || sl <= 0) return;

   double precio = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double lotes = Lotes(dir, precio, sl);
   if(lotes <= 0) return;
   if(trade.Buy(lotes, _Symbol, 0, sl, 0, "noche") && trade.ResultRetcode() == TRADE_RETCODE_DONE)
     {
      g_opsHoy++;
      GuardarGV("ops_hoy", g_opsHoy);
     }
  }

//+------------------------------------------------------------------+
double Lotes(int dir, double precio, double sl)
  {
   double paso = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotes = InpLotesFijos;
   if(lotes <= 0)
     {
      double perdida1 = 0;
      if(!OrderCalcProfit(ORDER_TYPE_BUY, _Symbol, 1.0, precio, sl, perdida1) || perdida1 >= 0) return 0;
      double riesgo = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiesgoPct / 100.0;
      lotes = riesgo / -perdida1;
     }
   lotes = MathFloor(lotes / paso) * paso;
   if(lotes < minL) return 0;
   return NormalizeDouble(MathMin(lotes, maxL), 2);
  }

//+------------------------------------------------------------------+
void NuevoDiaSiToca()
  {
   datetime ahora = TimeCurrent();
   datetime dia = ahora - (ahora % 86400);
   if(dia == g_dia) return;
   g_dia = dia;
   if((datetime)CargarGV("dia", 0) == dia)
     {
      g_baseDia = CargarGV("base_dia", AccountInfoDouble(ACCOUNT_BALANCE));
      g_paradoDia = CargarGV("parado_dia", 0) > 0;
      g_opsHoy = (int)CargarGV("ops_hoy", 0);
     }
   else
     {
      g_baseDia = MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY));
      g_paradoDia = false;
      g_opsHoy = 0;
      GuardarGV("dia", (double)dia);
      GuardarGV("base_dia", g_baseDia);
      GuardarGV("parado_dia", 0);
      GuardarGV("ops_hoy", 0);
     }
  }

bool ComprobarLimites()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!g_paradoTotal && eq <= g_inicial * (1 - InpPerdidaTotalPct / 100.0))
     {
      g_paradoTotal = true;
      GuardarGV("parado_total", 1);
      Avisar("Corte TOTAL alcanzado: EA parado hasta revisión manual");
     }
   if(!g_paradoTotal && InpObjetivoPct > 0 && eq >= g_inicial * (1 + InpObjetivoPct / 100.0))
     {
      g_paradoTotal = true;
      GuardarGV("parado_total", 1);
      Avisar("Objetivo del reto alcanzado: EA parado");
     }
   if(!g_paradoDia && eq <= g_baseDia - g_inicial * InpPerdidaDiariaPct / 100.0)
     {
      g_paradoDia = true;
      GuardarGV("parado_dia", 1);
      Avisar("Corte DIARIO alcanzado: sin operar hasta mañana");
     }
   if(g_paradoDia || g_paradoTotal)
     {
      CerrarTodo("límite de la cuenta");
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
ulong PosicionPropia()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk != 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         return tk;
     }
   return 0;
  }

void CerrarTodo(string motivo)
  {
   static datetime ultimoIntento = 0;
   if(TimeCurrent() - ultimoIntento < 1) return;
   ultimoIntento = TimeCurrent();
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk != 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         if(!trade.PositionClose(tk))
            PrintFormat("No se pudo cerrar %I64u (%s): %d", tk, motivo, trade.ResultRetcode());
     }
  }

bool VelaNueva()
  {
   static datetime ultima = 0;
   datetime v = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(v == ultima) return false;
   ultima = v;
   return true;
  }

void Avisar(string texto)
  {
   Print(texto);
   if(!MQLInfoInteger(MQL_TESTER)) { Alert(texto); SendNotification(_Symbol + ": " + texto); }
  }

double CargarGV(string clave, double defecto)
  {
   string n = g_prefijo + clave;
   return GlobalVariableCheck(n) ? GlobalVariableGet(n) : defecto;
  }

void GuardarGV(string clave, double valor) { GlobalVariableSet(g_prefijo + clave, valor); }

//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
  {
   if(!InpRegistrarCSV || trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;
   string nombre = MQLInfoString(MQL_PROGRAM_NAME) + "_" + _Symbol + "_ops.csv";
   int f = FileOpen(nombre, FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ';');
   if(f == INVALID_HANDLE) return;
   if(FileSize(f) == 0) FileWrite(f, "cierre", "posicion", "tipo", "volumen", "precio", "beneficio", "comision", "swap");
   FileSeek(f, 0, SEEK_END);
   FileWrite(f, TimeToString((datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME), TIME_DATE | TIME_SECONDS),
             HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID),
             HistoryDealGetInteger(trans.deal, DEAL_TYPE) == DEAL_TYPE_SELL ? "cierra_largo" : "cierra_corto",
             HistoryDealGetDouble(trans.deal, DEAL_VOLUME), HistoryDealGetDouble(trans.deal, DEAL_PRICE),
             HistoryDealGetDouble(trans.deal, DEAL_PROFIT), HistoryDealGetDouble(trans.deal, DEAL_COMMISSION),
             HistoryDealGetDouble(trans.deal, DEAL_SWAP));
   FileClose(f);
  }
//+------------------------------------------------------------------+
