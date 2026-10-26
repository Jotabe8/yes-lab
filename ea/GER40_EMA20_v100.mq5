//+------------------------------------------------------------------+
//| GER40_EMA20_v100.mq5                                             |
//| Retroceso a EMA20 con tendencia en la apertura del DAX (M30),    |
//| gestión NNFX de corredor: SL 1,5 ATR, BE a +1 ATR, trailing 2 ATR.|
//| Réplica de informes/scalping_nnfx/coste_bajo.py (E1, G2, sin     |
//| filtro de coste). Hora del servidor FTMO (NY+7).                 |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.00"
#property strict
#include <Trade/Trade.mqh>

input group "Señal"
input ENUM_TIMEFRAMES InpTF        = PERIOD_M30; // Temporalidad de la señal
input int    InpEmaFast            = 20;         // EMA de retroceso
input int    InpEmaMid             = 50;         // EMA de tendencia rápida
input int    InpEmaSlow            = 200;        // EMA de tendencia lenta
input int    InpAtrPeriod          = 14;         // ATR
input group "Horario (hora servidor)"
input int    InpStartMin           = 600;        // Inicio de la ventana de señal (10:00 = 600)
input int    InpWindowMin          = 90;         // Duración de la ventana (min)
input int    InpSessionEndMin      = 1105;       // Cierre forzoso (18:25 = 1105)
input int    InpMaxTradesDay       = 2;          // Máximo de operaciones por día
input group "Gestión"
input double InpRiskPct            = 1.0;        // Riesgo por operación (% del balance)
input double InpSlAtr              = 1.5;        // Stop en ATR
input double InpBeAtr              = 1.0;        // Mover a BE al ganar estos ATR
input double InpTrailAtr           = 2.0;        // Trailing en ATR (al cierre de vela, tras BE)
input double InpMaxSpreadPts       = 0;          // Spread máximo para entrar en puntos (0 = sin límite)
input long   InpMagic              = 20261026;

CTrade trade;
int hEf, hEm, hEs, hAtr;
datetime lastBar = 0;
int tradesToday = 0, dayKey = -1;
double entryAtr = 0;   // ATR de la vela de señal de la posición abierta
bool   beDone = false;

int MinuteOfDay(datetime t) { MqlDateTime s; TimeToStruct(t, s); return s.hour * 60 + s.min; }
int DayOf(datetime t)       { MqlDateTime s; TimeToStruct(t, s); return s.year * 1000 + s.day_of_year; }

int OnInit()
{
   hEf  = iMA(_Symbol, InpTF, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
   hEm  = iMA(_Symbol, InpTF, InpEmaMid,  0, MODE_EMA, PRICE_CLOSE);
   hEs  = iMA(_Symbol, InpTF, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);
   hAtr = iATR(_Symbol, InpTF, InpAtrPeriod);
   if(hEf == INVALID_HANDLE || hEm == INVALID_HANDLE || hEs == INVALID_HANDLE || hAtr == INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hEf); IndicatorRelease(hEm); IndicatorRelease(hEs); IndicatorRelease(hAtr);
}

bool Val(int h, int shift, double &v) { double b[]; if(CopyBuffer(h, 0, shift, 1, b) != 1) return false; v = b[0]; return true; }

bool HasPosition(ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(PositionSelectByTicket(t) && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
      { ticket = t; return true; }
   }
   return false;
}

double LotsFor(double slDist)
{
   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0 || ts <= 0 || slDist <= 0) return 0;
   double money = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPct / 100.0;
   double lots = money / (slDist / ts * tv);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lots = MathFloor(lots / step) * step;
   return (lots < mn) ? 0 : MathMin(lots, mx);
}

void OnTick()
{
   datetime now = TimeCurrent();
   int mod = MinuteOfDay(now), dk = DayOf(now);
   if(dk != dayKey) { dayKey = dk; tradesToday = 0; }
   ulong tk = 0; bool open = HasPosition(tk);

   // cierre forzoso al final de la sesión
   if(open && mod >= InpSessionEndMin) { trade.PositionClose(tk); return; }

   // BE en cada tick al alcanzar +1 ATR (en Python: máximo/mínimo del minuto toca el objetivo)
   if(open && !beDone && entryAtr > 0 && PositionSelectByTicket(tk))
   {
      long   typ = PositionGetInteger(POSITION_TYPE);
      double ent = PositionGetDouble(POSITION_PRICE_OPEN), sl = PositionGetDouble(POSITION_SL);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(typ == POSITION_TYPE_BUY && bid >= ent + InpBeAtr * entryAtr && sl < ent) { if(trade.PositionModify(tk, ent, 0)) beDone = true; }
      if(typ == POSITION_TYPE_SELL && ask <= ent - InpBeAtr * entryAtr && (sl > ent || sl == 0)) { if(trade.PositionModify(tk, ent, 0)) beDone = true; }
   }

   // todo lo demás, solo al abrir vela nueva de la temporalidad de señal
   datetime bt = iTime(_Symbol, InpTF, 0);
   if(bt == lastBar) return;
   lastBar = bt;

   double ef, em, es, atr;
   if(!Val(hEf, 1, ef) || !Val(hEm, 1, em) || !Val(hEs, 1, es) || !Val(hAtr, 1, atr) || atr <= 0) return;
   double o1 = iOpen(_Symbol, InpTF, 1), h1 = iHigh(_Symbol, InpTF, 1), l1 = iLow(_Symbol, InpTF, 1), c1 = iClose(_Symbol, InpTF, 1);

   // trailing al cierre de vela, solo tras BE
   if(open && beDone && PositionSelectByTicket(tk))
   {
      long typ = PositionGetInteger(POSITION_TYPE); double sl = PositionGetDouble(POSITION_SL);
      double ns = (typ == POSITION_TYPE_BUY) ? c1 - InpTrailAtr * atr : c1 + InpTrailAtr * atr;
      ns = NormalizeDouble(ns, _Digits);
      if((typ == POSITION_TYPE_BUY && ns > sl) || (typ == POSITION_TYPE_SELL && ns < sl)) trade.PositionModify(tk, ns, 0);
   }
   if(open) return;

   // la vela de señal debe cerrar dentro de la ventana y dentro de la sesión
   int closeMin = MinuteOfDay(iTime(_Symbol, InpTF, 1)) + PeriodSeconds(InpTF) / 60;
   if(closeMin < InpStartMin + PeriodSeconds(InpTF) / 60 || closeMin > InpStartMin + InpWindowMin || mod >= InpSessionEndMin) return;
   if(tradesToday >= InpMaxTradesDay) return;

   int dir = 0;
   if(em > es && l1 <= ef && c1 > ef && c1 > o1) dir = 1;
   if(em < es && h1 >= ef && c1 < ef && c1 < o1) dir = -1;
   if(dir == 0) return;
   if(InpMaxSpreadPts > 0 && SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpreadPts) return;

   double slDist = InpSlAtr * atr, lots = LotsFor(slDist);
   if(lots <= 0) return;
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   bool ok = (dir == 1) ? trade.Buy(lots, _Symbol, ask, NormalizeDouble(ask - slDist, _Digits), 0, "GER40 EMA20")
                        : trade.Sell(lots, _Symbol, bid, NormalizeDouble(bid + slDist, _Digits), 0, "GER40 EMA20");
   if(ok) { tradesToday++; entryAtr = atr; beDone = false; }
}
//+------------------------------------------------------------------+
