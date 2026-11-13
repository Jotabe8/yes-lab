//+------------------------------------------------------------------+
//| PlantillaPropEA.mq5                                              |
//| Plantilla para EAs de prop firm (FTMO). Solo hay que rellenar     |
//| Senal(). Todo lo demás (riesgo, límites FTMO, horario, spread,    |
//| registro de operaciones para comparar con Python) ya está.        |
//| Ver metodo/METODO.md, paso P6.                                    |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.00"

#include <Trade/Trade.mqh>

//--- Riesgo
input double InpRiesgoPct        = 1.0;    // Riesgo por operación (% del balance)
input double InpLotesFijos       = 0.0;    // >0: lotes fijos (ignora el riesgo)
//--- Límites de la cuenta (por debajo de los de FTMO, con margen por huecos)
input double InpPerdidaDiariaPct = 4.0;    // Corte diario interno (FTMO 2-Step: 5 %)
input double InpPerdidaTotalPct  = 8.0;    // Corte total interno (FTMO: 10 % del inicial)
input double InpBalanceInicial   = 0.0;    // Balance inicial de la cuenta (0 = el actual al arrancar)
input double InpObjetivoPct      = 0.0;    // >0: deja de operar al llegar al objetivo del reto
//--- Horario (hora del servidor; FTMO usa la hora de Praga)
input int    InpHoraInicio       = 0;      // Primera hora en que puede abrir
input int    InpHoraFin          = 24;     // Ya no abre a partir de esta hora
input int    InpHoraCierre       = -1;     // >=0: cierra todo a esta hora
input bool   InpCerrarViernes    = false;  // Cierra todo el viernes a InpHoraCierre (o 22h)
//--- Filtros
input int    InpMaxOpsDia        = 2;      // Máximo de entradas por día
input double InpMaxSpreadPuntos  = 0;      // >0: no abre si el spread supera estos puntos
input long   InpMagic            = 260001; // Número mágico (uno por EA y símbolo)
input bool   InpRegistrarCSV     = true;   // Guarda cada operación cerrada en Common/Files

CTrade trade;
string g_prefijo;          // clave de las variables globales de esta instancia
datetime g_dia = 0;        // inicio del día de servidor en curso
double g_baseDia = 0;      // max(balance, equity) al empezar el día
bool   g_paradoDia = false;
bool   g_paradoTotal = false;
int    g_opsHoy = 0;
double g_inicial = 0;

//+------------------------------------------------------------------+
//| RELLENAR: devuelve +1 compra, -1 venta, 0 nada.                   |
//| sl y tp son PRECIOS. Se llama una vez por vela nueva.             |
//+------------------------------------------------------------------+
int Senal(double &sl, double &tp)
  {
   sl = 0; tp = 0;
   // Ejemplo: cruce de precio sobre EMA(20) con stop a 1 ATR(14) y objetivo a 2 ATR.
   // Sustituir por la regla validada en Python, sin añadir nada que no se probó allí.
   static int hEma = INVALID_HANDLE, hAtr = INVALID_HANDLE;
   if(hEma == INVALID_HANDLE) hEma = iMA(_Symbol, PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);
   if(hAtr == INVALID_HANDLE) hAtr = iATR(_Symbol, PERIOD_CURRENT, 14);
   double ema[], atr[];
   if(CopyBuffer(hEma, 0, 1, 2, ema) < 2 || CopyBuffer(hAtr, 0, 1, 1, atr) < 1) return 0;
   double c1 = iClose(_Symbol, PERIOD_CURRENT, 1), c2 = iClose(_Symbol, PERIOD_CURRENT, 2);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   // ArraySetAsSeries no se usa: ema[1] es la vela 1 (la última cerrada), ema[0] la vela 2
   if(c2 <= ema[0] && c1 > ema[1]) { sl = ask - atr[0]; tp = ask + 2 * atr[0]; return +1; }
   if(c2 >= ema[0] && c1 < ema[1]) { sl = bid + atr[0]; tp = bid - 2 * atr[0]; return -1; }
   return 0;
  }

//+------------------------------------------------------------------+
//| RELLENAR (opcional): gestión de la posición abierta en cada tick |
//| (break-even, trailing, salida por tiempo).                        |
//+------------------------------------------------------------------+
void Gestionar(ulong ticket)
  {
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(20);
   g_prefijo = StringFormat("pea_%I64d_%I64d_%s_", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, _Symbol);
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

   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   int horaCierre = InpHoraCierre >= 0 ? InpHoraCierre : 22;
   if((InpHoraCierre >= 0 && t.hour >= InpHoraCierre) ||
      (InpCerrarViernes && t.day_of_week == 5 && t.hour >= horaCierre))
     {
      CerrarTodo("cierre horario");
      return;
     }

   ulong ticket = PosicionPropia();
   if(ticket != 0) { Gestionar(ticket); return; }

   if(!VelaNueva()) return;
   if(t.hour < InpHoraInicio || t.hour >= InpHoraFin) return;
   if(g_opsHoy >= InpMaxOpsDia) return;
   if(InpMaxSpreadPuntos > 0 && SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPuntos) return;

   double sl, tp;
   int dir = Senal(sl, tp);
   if(dir == 0 || sl <= 0) return;

   double precio = dir > 0 ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double lotes = Lotes(dir, precio, sl);
   if(lotes <= 0) return;
   bool ok = dir > 0 ? trade.Buy(lotes, _Symbol, 0, sl, tp, "plantilla")
                     : trade.Sell(lotes, _Symbol, 0, sl, tp, "plantilla");
   if(ok && trade.ResultRetcode() == TRADE_RETCODE_DONE)
     {
      g_opsHoy++;
      GuardarGV("ops_hoy", g_opsHoy);
     }
  }

//+------------------------------------------------------------------+
//| Lotes para arriesgar InpRiesgoPct del balance hasta el stop       |
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
      ENUM_ORDER_TYPE tipo = dir > 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      if(!OrderCalcProfit(tipo, _Symbol, 1.0, precio, sl, perdida1) || perdida1 >= 0) return 0;
      double riesgo = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiesgoPct / 100.0;
      lotes = riesgo / -perdida1;
     }
   lotes = MathFloor(lotes / paso) * paso;  // hacia abajo: nunca arriesgar de más
   if(lotes < minL) return 0;               // el stop es demasiado ancho para el riesgo
   return NormalizeDouble(MathMin(lotes, maxL), 2);
  }

//+------------------------------------------------------------------+
//| Día de servidor, base diaria y límites (estado persistente)       |
//+------------------------------------------------------------------+
void NuevoDiaSiToca()
  {
   datetime ahora = TimeCurrent();
   datetime dia = ahora - (ahora % 86400);
   if(dia == g_dia) return;
   g_dia = dia;
   if((datetime)CargarGV("dia", 0) == dia)   // reinicio dentro del mismo día: recuperar
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
   // FTMO mide la pérdida diaria como % del balance INICIAL desde el balance del inicio del día
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
//| Utilidades                                                        |
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
   if(TimeCurrent() - ultimoIntento < 1) return;   // reintento como mucho una vez por segundo
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
//| Registro de operaciones cerradas para comparar con Python:        |
//| Common/Files/<EA>_<símbolo>_ops.csv                               |
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
