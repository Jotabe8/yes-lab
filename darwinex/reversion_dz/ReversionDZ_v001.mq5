//+------------------------------------------------------------------+
//| ReversionDZ_v001.mq5                                              |
//| Reversión de varios días en índices US para Darwinex Zero.        |
//| Regla validada en Python (darwinex/reversion_dz/PREREGISTRO.md):  |
//|  - A las 15:58 NY, con la sesión de contado 9:30-16:00 en curso:  |
//|    IBS = (C-L)/(H-L) < 0,20 y C < cierre de ayer -> largo.        |
//|  - Salida a las 15:58 NY del primer día con C > máximo de ayer,   |
//|    o al cumplir 5 sesiones. Sin stop. Una posición por símbolo.   |
//|  - Tamaño: 1 ATR20 de sesión en contra = InpRiesgoATRPct.         |
//| Un gráfico por símbolo (ES, NQ, YM, RTY o sus CFD). Cualquier TF. |
//| No añadir nada que no se probó en Python.                         |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.02"
#include <Trade/Trade.mqh>

input double InpRiesgoATRPct  = 0.30;   // % del balance que se pierde si el precio cae 1 ATR20
input double InpLotesFijos    = 0.0;    // >0: lotes fijos (ignora el riesgo)
input double InpIBS           = 0.20;   // Umbral IBS de entrada
input int    InpMaxSesiones   = 5;      // Salida por tiempo (sesiones de contado)
input int    InpATR           = 20;     // Periodo del ATR de sesión
input int    InpServidorMenosNY = 7;    // Horas servidor - NY. FTMO/Dukascopy: 7 todo el año. Comprobar en DZ (si su servidor sigue el horario de la UE, 6 unas 3 semanas al año)
input int    InpMinutoSenalNY = 958;    // Hora NY de la señal en HHMM (15:58)
input long   InpMagic         = 270001; // Número mágico (uno por símbolo)
input bool   InpRegistrarCSV  = true;   // Guarda cada operación cerrada en Common/Files

CTrade trade;
string g_pref;

//--- hora NY y conversión a hora del servidor
datetime NY(datetime srv)            { return srv - InpServidorMenosNY * 3600; }
datetime Srv(datetime ny)            { return ny + InpServidorMenosNY * 3600; }
datetime DiaNY(datetime srv)         { datetime n = NY(srv); return n - (n % 86400); }
int      HHMM(datetime t)            { MqlDateTime s; TimeToStruct(t, s); return s.hour * 100 + s.min; }

//+------------------------------------------------------------------+
//| Sesión de contado de un día NY: H, L, C con velas M1 desde 9:30   |
//| hasta 'finHHMM' (exclusivo). Devuelve false si no hay datos o la  |
//| sesión no llegó a esa hora (festivo, media sesión).               |
//+------------------------------------------------------------------+
bool Sesion(datetime diaNY, int finHHMM, double &h, double &l, double &c)
  {
   datetime ini = Srv(diaNY + 9 * 3600 + 30 * 60);
   datetime fin = Srv(diaNY + (finHHMM / 100) * 3600 + (finHHMM % 100) * 60);
   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, ini, fin - 60, r);
   if(n <= 0) return false;
   if(r[n - 1].time < fin - 60 * 5) return false;          // la sesión acabó antes (media sesión)
   h = r[0].high; l = r[0].low;
   for(int i = 1; i < n; i++) { h = MathMax(h, r[i].high); l = MathMin(l, r[i].low); }
   c = r[n - 1].close;
   return true;
  }

//--- sesión completa anterior a diaNY (busca hasta 10 días atrás)
bool SesionAnterior(datetime diaNY, datetime &d, double &h, double &l, double &c)
  {
   for(int k = 1; k <= 10; k++)
     {
      d = diaNY - k * 86400;
      if(Sesion(d, 1600, h, l, c)) return true;
     }
   return false;
  }

//--- ATR de sesión: TR de hoy (parcial) + InpATR-1 sesiones completas anteriores
double ATRSesion(datetime diaNY, double h0, double l0)
  {
   double tr[]; ArrayResize(tr, InpATR);
   datetime d; double h, l, c;
   if(!SesionAnterior(diaNY, d, h, l, c)) return 0;
   tr[0] = MathMax(h0 - l0, MathMax(MathAbs(h0 - c), MathAbs(l0 - c)));
   datetime cur = d; double hc = h, lc = l;
   for(int i = 1; i < InpATR; i++)
     {
      datetime dp; double hp, lp, cp;
      if(!SesionAnterior(cur, dp, hp, lp, cp)) return 0;
      tr[i] = MathMax(hc - lc, MathMax(MathAbs(hc - cp), MathAbs(lc - cp)));
      cur = dp; hc = hp; lc = lp;
     }
   double s = 0; for(int i = 0; i < InpATR; i++) s += tr[i];
   return s / InpATR;
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   g_pref = StringFormat("rdz_%I64d_%I64d_%s_", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, _Symbol);
   if(MQLInfoInteger(MQL_TESTER)) GlobalVariablesDeleteAll(g_pref);   // el tester comparte variables globales entre pasadas
   return INIT_SUCCEEDED;
  }

double GV(string k, double def) { string n = g_pref + k; return GlobalVariableCheck(n) ? GlobalVariableGet(n) : def; }
void   GVs(string k, double v)  { GlobalVariableSet(g_pref + k, v); }

ulong Posicion()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk != 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic) return tk;
     }
   return 0;
  }

//--- sesiones de contado completas desde el día siguiente a la entrada hasta ayer, más hoy
int SesionesDesde(datetime entradaNY, datetime hoy)
  {
   int n = 1;                                                     // hoy
   double h, l, c;
   for(datetime d = entradaNY + 86400; d < hoy; d += 86400)
      if(Sesion(d, 1600, h, l, c)) n++;
   return n;
  }

bool OrdenOk(uint rc) { return rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_PLACED || rc == TRADE_RETCODE_DONE_PARTIAL; }

//+------------------------------------------------------------------+
void OnTick()
  {
   datetime ahora = TimeCurrent();
   int hm = HHMM(NY(ahora));
   if(hm < InpMinutoSenalNY || hm >= 1600) return;              // solo entre 15:58 y 16:00 NY
   datetime hoy = DiaNY(ahora);
   if((datetime)GV("evaluado", 0) == hoy) return;               // una decisión por día
   static datetime ultimoIntento = 0;                           // reintentos como mucho cada 10 s
   if(ahora - ultimoIntento < 10) return;
   ultimoIntento = ahora;
   // Datos: sesión de hoy hasta la señal + precio actual; sesión completa de ayer
   double h0, l0, c0;
   if(!Sesion(hoy, InpMinutoSenalNY, h0, l0, c0)) return;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(bid <= 0) return;
   c0 = bid; h0 = MathMax(h0, bid); l0 = MathMin(l0, bid);
   datetime dAyer; double h1, l1, c1;
   if(!SesionAnterior(hoy, dAyer, h1, l1, c1)) return;

   ulong tk = Posicion();
   if(tk != 0)
     {
      int ses = SesionesDesde((datetime)GV("entrada", (double)hoy), hoy);
      if(c0 > h1 || ses >= InpMaxSesiones)
        {
         if(!trade.PositionClose(tk) || !OrdenOk(trade.ResultRetcode()))
           { PrintFormat("No se pudo cerrar %I64u: %d (reintento)", tk, trade.ResultRetcode()); return; }
         PrintFormat("Salida: C %.2f, máximo de ayer %.2f, sesiones %d", c0, h1, ses);
        }
      GVs("evaluado", (double)hoy);                               // sin reentrada el día de salida (igual que Python)
      GlobalVariablesFlush();
      return;
     }

   if(h0 <= l0) { GVs("evaluado", (double)hoy); return; }
   double ibs = (c0 - l0) / (h0 - l0);
   if(!(ibs < InpIBS && c0 < c1)) { GVs("evaluado", (double)hoy); return; }
   double atr = ATRSesion(hoy, h0, l0);
   if(atr <= 0) return;                                           // historial M1 incompleto: reintenta
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double lotes = InpLotesFijos;
   if(lotes <= 0)
     {
      double p1 = 0;
      if(!OrderCalcProfit(ORDER_TYPE_BUY, _Symbol, 1.0, ask, ask - atr, p1) || p1 >= 0) return;
      lotes = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiesgoATRPct / 100.0 / -p1;
     }
   double paso = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   lotes = MathFloor(lotes / paso) * paso;
   if(lotes < minL) { PrintFormat("Riesgo insuficiente para el lote mínimo (ATR %.2f)", atr); GVs("evaluado", (double)hoy); return; }
   lotes = MathMin(lotes, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX));
   PrintFormat("Señal: IBS %.3f C %.2f < C ayer %.2f, ATR %.2f, lotes %.2f", ibs, c0, c1, atr, lotes);
   GVs("entrada", (double)hoy);                                   // estado antes de enviar: el CSV y la salida lo usan
   GVs("atr", atr);
   if(trade.Buy(lotes, _Symbol, 0, 0, 0, "reversion") && OrdenOk(trade.ResultRetcode()))
      GVs("evaluado", (double)hoy);
   else PrintFormat("Compra rechazada: %d (reintento)", trade.ResultRetcode());
   GlobalVariablesFlush();
  }

//+------------------------------------------------------------------+
//| CSV compatible con metodo/comparar_ops.py (formato plantilla):    |
//| sl_inicial = entrada - ATR (virtual, no se envía) para que        |
//| r_bruto = movimiento / ATR20, igual que Python.                   |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
  {
   if(!InpRegistrarCSV || trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;
   datetime cierre = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
   long   pos   = HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   double vol   = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
   double prec  = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double benef = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);
   double comi  = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
   double swap  = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
   double atr   = GV("atr", 0);
   datetime apertura = 0; double p_ent = 0;
   if(HistorySelectByPosition(pos))
      for(int i = 0; i < HistoryDealsTotal(); i++)
        {
         ulong d = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(d, DEAL_ENTRY) != DEAL_ENTRY_IN) continue;
         apertura = (datetime)HistoryDealGetInteger(d, DEAL_TIME);
         p_ent = HistoryDealGetDouble(d, DEAL_PRICE);
         comi += HistoryDealGetDouble(d, DEAL_COMMISSION);
         break;
        }
   double r = atr > 0 ? (prec - p_ent) / atr : 0;
   string nombre = MQLInfoString(MQL_PROGRAM_NAME) + "_" + _Symbol + "_ops.csv";
   int f = FileOpen(nombre, FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ';');
   if(f == INVALID_HANDLE) return;
   if(FileSize(f) == 0) FileWrite(f, "cierre", "posicion", "tipo", "volumen", "precio", "beneficio", "comision", "swap",
                                  "apertura", "precio_entrada", "sl_inicial", "r_bruto");
   FileSeek(f, 0, SEEK_END);
   FileWrite(f, TimeToString(cierre, TIME_DATE | TIME_SECONDS), pos, "cierra_largo", vol, prec, benef, comi, swap,
             TimeToString(apertura, TIME_DATE | TIME_SECONDS), DoubleToString(p_ent, _Digits),
             DoubleToString(p_ent - atr, _Digits), DoubleToString(r, 3));
   FileClose(f);
  }
//+------------------------------------------------------------------+
