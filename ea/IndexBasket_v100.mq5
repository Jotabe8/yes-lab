//+------------------------------------------------------------------+
//| IndexBasket_v100.mq5                                             |
//| Cesta larga de índices con volatilidad objetivo (2026-10-26).    |
//| Réplica de informes/prima_indices/prima.py en yes-lab:           |
//|  - Largo en cada índice si el cierre D1 de ayer > SMA(200) D1;   |
//|    si no, en liquidez (nunca corto).                             |
//|  - Nominal por índice = capital * RiskMult * (TargetVol / vol20) |
//|    / nº de índices, con palanca por índice <= MaxLevPerIndex.    |
//|  - vol20 = desviación de 20 retornos D1 cerrados * sqrt(252).   |
//|  - Reequilibrio una vez al día a RebalanceHour (hora servidor),  |
//|    solo si el tamaño objetivo difiere más de RebalanceBand.      |
//|  - Nunca abre/aumenta en viernes desde FridayCutoffHour (regla   |
//|    de gap de FTMO: no abrir 2 h antes de pausas largas).         |
//|  - Freno diario: si la equity cae DailyStopPct desde el inicio   |
//|    del día, cierra todo y no opera hasta el día siguiente.       |
//| Cuenta prevista: FTMO Swing (mantiene fines de semana).          |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.00"
#include <Trade/Trade.mqh>

input string Symbols          = "US500.cash,US100.cash,US30.cash,GER40.cash,UK100.cash,JP225.cash";
input double RiskMult         = 1.0;    // 1.0 = vol de cartera ≈ 7 % anual (probado); 1.5 ≈ 10 %
input double TargetVol        = 0.10;   // volatilidad objetivo anual por índice
input double MaxLevPerIndex   = 2.0;    // tope de nominal/capital por índice (antes de dividir por nº)
input int    SmaPeriod        = 200;
input int    VolPeriod        = 20;
input int    RebalanceHour    = 16;     // hora servidor (abiertos EU y EE. UU.)
input double RebalanceBand    = 0.20;   // reequilibra si |objetivo-actual|/objetivo > 20 %
input int    FridayCutoffHour = 18;     // viernes desde esta hora no abre ni aumenta
input double DailyStopPct     = 2.5;    // % de caída de equity en el día que cierra todo (1-Step: 3 %)
input long   Magic            = 26102601;

CTrade trade;
string syms[];
int    nsym = 0;
int    lastRebalanceDay = -1;
int    dayKey = -1;
double dayStartEquity = 0;
bool   haltedToday = false;

int DayKeyOf(datetime t) { MqlDateTime s; TimeToStruct(t, s); return s.year * 1000 + s.day_of_year; }

int OnInit()
{
   nsym = StringSplit(Symbols, ',', syms);
   for(int i = 0; i < nsym; i++)
   {
      StringTrimLeft(syms[i]); StringTrimRight(syms[i]);
      if(!SymbolSelect(syms[i], true)) { PrintFormat("No existe el símbolo %s", syms[i]); return INIT_PARAMETERS_INCORRECT; }
   }
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints(50);
   EventSetTimer(60);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { EventKillTimer(); }

// Señal y volatilidad con barras D1 cerradas (índice 1 = ayer)
bool Signal(const string s, bool &longOk, double &vol)
{
   double c[];
   int need = MathMax(SmaPeriod, VolPeriod + 1) + 1;
   ArraySetAsSeries(c, true);
   if(CopyClose(s, PERIOD_D1, 1, need, c) < need) return false;
   double sma = 0; for(int i = 0; i < SmaPeriod; i++) sma += c[i]; sma /= SmaPeriod;
   longOk = c[0] > sma;
   double r[]; ArrayResize(r, VolPeriod); double m = 0;
   for(int i = 0; i < VolPeriod; i++) { r[i] = c[i] / c[i + 1] - 1.0; m += r[i]; }
   m /= VolPeriod; double v = 0;
   for(int i = 0; i < VolPeriod; i++) v += (r[i] - m) * (r[i] - m);
   vol = MathSqrt(v / (VolPeriod - 1)) * MathSqrt(252.0);
   return vol > 0;
}

// Valor nominal (divisa de la cuenta) de 1 lote
double NotionalPerLot(const string s)
{
   double tv = SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(s, SYMBOL_TRADE_TICK_SIZE);
   double px = SymbolInfoDouble(s, SYMBOL_BID);
   if(ts <= 0 || px <= 0) return 0;
   return px * tv / ts;
}

double CurrentLots(const string s)
{
   double lots = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(!PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL) != s || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      lots += (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1) * PositionGetDouble(POSITION_VOLUME);
   }
   return lots;
}

double NormLots(const string s, double lots)
{
   double step = SymbolInfoDouble(s, SYMBOL_VOLUME_STEP), mn = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(s, SYMBOL_VOLUME_MAX);
   if(step <= 0) return 0;
   lots = MathFloor(lots / step) * step;
   if(lots < mn) return 0;
   return MathMin(lots, mx);
}

// Reduce la posición del símbolo en 'lots' (cierra posiciones de la más nueva a la más vieja)
void Reduce(const string s, double lots)
{
   for(int i = PositionsTotal() - 1; i >= 0 && lots > 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(!PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL) != s || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      double v = PositionGetDouble(POSITION_VOLUME);
      double c = NormLots(s, MathMin(v, lots));
      if(c <= 0) break;
      if(c >= v) trade.PositionClose(tk); else trade.PositionClosePartial(tk, c);
      lots -= c;
   }
}

void CloseAll()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(PositionSelectByTicket(tk) && PositionGetInteger(POSITION_MAGIC) == Magic) trade.PositionClose(tk);
   }
}

void Rebalance(bool fridayLate)
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   for(int i = 0; i < nsym; i++)
   {
      string s = syms[i];
      if(!SymbolInfoInteger(s, SYMBOL_TRADE_MODE)) continue;
      bool longOk; double vol;
      if(!Signal(s, longOk, vol)) { PrintFormat("%s: sin datos D1 suficientes", s); continue; }
      double lev = MathMin(TargetVol / vol, MaxLevPerIndex);
      double npl = NotionalPerLot(s);
      if(npl <= 0) continue;
      double target = longOk ? NormLots(s, eq * RiskMult * lev / nsym / npl) : 0;
      double cur = CurrentLots(s);
      if(target == 0 && cur > 0) { Reduce(s, cur); continue; }
      if(target == 0) continue;
      double diff = target - cur;
      if(MathAbs(diff) / target <= RebalanceBand) continue;
      if(diff > 0)
      {
         if(fridayLate) continue;                              // no aumentar antes del fin de semana
         double add = NormLots(s, diff);
         if(add > 0) trade.Buy(add, s, 0, 0, 0, "IndexBasket");
      }
      else Reduce(s, -diff);
   }
}

void Tick()
{
   datetime now = TimeCurrent();
   int dk = DayKeyOf(now);
   if(dk != dayKey) { dayKey = dk; dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY); haltedToday = false; }
   if(!haltedToday && dayStartEquity > 0 && AccountInfoDouble(ACCOUNT_EQUITY) <= dayStartEquity * (1 - DailyStopPct / 100.0))
   {
      CloseAll(); haltedToday = true;
      PrintFormat("Freno diario: equity %.2f (inicio del día %.2f). Cerrado todo.", AccountInfoDouble(ACCOUNT_EQUITY), dayStartEquity);
   }
   if(haltedToday) return;
   MqlDateTime t; TimeToStruct(now, t);
   if(t.day_of_week == 0 || t.day_of_week == 6) return;
   if(t.hour != RebalanceHour || lastRebalanceDay == dk) return;
   lastRebalanceDay = dk;
   Rebalance(t.day_of_week == 5 && t.hour >= FridayCutoffHour);
}

void OnTimer() { Tick(); }
void OnTick()  { Tick(); }
