//+------------------------------------------------------------------+
//| TendenciaCripto_v001.mq5                                          |
//| v19 (metodo/v19/PREREGISTRO.md): tendencia semanal en una cesta   |
//| cripto. Cada lunes, con el cierre D1 del domingo: comprado 7 días |
//| cada símbolo cuyo rendimiento de 28 días es > 0, si no fuera.      |
//| Tamaño: 1 sigma semanal = InpRiesgoPct del balance (sigma = desv.  |
//| de los rendimientos log diarios de los 30 días previos x raíz(7)). |
//| Un solo gráfico gestiona todos los símbolos. Límites FTMO y CSV de |
//| la plantilla (metodo/PlantillaPropEA.mq5).                         |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.02"

#include <Trade/Trade.mqh>

//--- Cesta y regla (lo probado en Python; no tocar sin volver al embudo)
input string InpSimbolos         = "BTCUSD,ETHUSD,LTCUSD,XRPUSD,BCHUSD,ADAUSD,DOGEUSD,DOTUSD,SOLUSD,AVAXUSD,LNKUSD,XLMUSD,ETCUSD,BNBUSD,UNIUSD,TRXUSD,NEARUSD,ATOMUSD,FILUSD,EOSUSD"; // nombres del bróker; los que no existan se ignoran
input int    InpLookbackDias     = 28;     // Rendimiento de N días naturales
input int    InpVolDias          = 30;     // Ventana de la volatilidad (días naturales)
input int    InpDiaRebalanceo    = 1;      // Día de la semana del servidor (1 = lunes)
input int    InpHoraRebalanceo   = 0;      // Hora del servidor del rebalanceo (tras el cierre D1 del domingo)
//--- Riesgo
input double InpRiesgoPct        = 0.2;    // % del balance por 1 sigma semanal y símbolo
input double InpExposicionMaxPct = 300.0;  // Tope de nocional total / balance (%), salvaguarda (no probado en Python: se avisa si actúa)
input int    InpMinHistoriaDias  = 60;     // Días de historia D1 antes de que un símbolo pueda entrar (como en Python)
//--- Límites de la cuenta (por debajo de los de FTMO)
input double InpPerdidaDiariaPct = 4.0;    // Corte diario interno (FTMO 2-Step: 5 %)
input double InpPerdidaTotalPct  = 8.0;    // Corte total interno (FTMO: 10 % del inicial)
input double InpBalanceInicial   = 0.0;    // Balance inicial de la cuenta (0 = el actual al arrancar)
input double InpObjetivoPct      = 0.0;    // >0: deja de operar al llegar al objetivo del reto
input long   InpMagic            = 261901; // Número mágico
input bool   InpRegistrarCSV     = true;   // CSV de rebalanceos y de operaciones en Common/Files

CTrade trade;
string g_sim[];
string g_prefijo;
datetime g_dia = 0;
double g_baseDia = 0;
bool   g_paradoDia = false;
bool   g_paradoTotal = false;
double g_inicial = 0;
// estado de la semana en curso por símbolo, para el CSV de R "de modelo" (comparable con Python)
double g_pEnt[];     // cierre D1 del domingo del rebalanceo
double g_sigma[];    // sigma semanal usada
int    g_senal[];    // 1 comprado, 0 fuera
double g_obj[];      // lotes objetivo de la semana
bool   g_pend[];     // orden pendiente de completar (mercado cerrado, rechazo...)

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   string partes[];
   int n = StringSplit(InpSimbolos, ',', partes);
   ArrayResize(g_sim, 0);
   for(int i = 0; i < n; i++)
     {
      string s = partes[i];
      StringTrimLeft(s); StringTrimRight(s);
      if(s == "") continue;
      if(!SymbolSelect(s, true)) { PrintFormat("Símbolo %s no existe en este bróker: se ignora", s); continue; }
      int k = ArraySize(g_sim); ArrayResize(g_sim, k + 1); g_sim[k] = s;
      PrintFormat("%s: contrato %.4f, paso %.4f, mín %.4f, swap largo %.4f (modo %d), spread %d puntos, dígitos %d",
                  s, SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE), SymbolInfoDouble(s, SYMBOL_VOLUME_STEP),
                  SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), SymbolInfoDouble(s, SYMBOL_SWAP_LONG),
                  (int)SymbolInfoInteger(s, SYMBOL_SWAP_MODE), (int)SymbolInfoInteger(s, SYMBOL_SPREAD),
                  (int)SymbolInfoInteger(s, SYMBOL_DIGITS));
     }
   if(ArraySize(g_sim) == 0) { Print("Ningún símbolo válido"); return INIT_PARAMETERS_INCORRECT; }
   if(ArraySize(g_sim) < 10) Avisar(StringFormat("Solo %d símbolos de la cesta existen en este bróker: revisar InpSimbolos", ArraySize(g_sim)));
   int m = ArraySize(g_sim);
   ArrayResize(g_pEnt, m); ArrayResize(g_sigma, m); ArrayResize(g_senal, m);
   ArrayResize(g_obj, m); ArrayResize(g_pend, m); ArrayInitialize(g_obj, 0); ArrayInitialize(g_pend, false);
   ArrayInitialize(g_pEnt, 0); ArrayInitialize(g_sigma, 0); ArrayInitialize(g_senal, 0);
   g_prefijo = StringFormat("tc_%I64d_%I64d_", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic);
   if(MQLInfoInteger(MQL_TESTER)) GlobalVariablesDeleteAll(g_prefijo);   // cada pasada del tester empieza limpia
   g_inicial = InpBalanceInicial > 0 ? InpBalanceInicial : CargarGV("inicial", AccountInfoDouble(ACCOUNT_BALANCE));
   GuardarGV("inicial", g_inicial);
   g_paradoTotal = CargarGV("parado_total", 0) > 0;
   for(int i = 0; i < m; i++)  // estado de la semana tras un reinicio
     {
      g_pEnt[i]  = CargarGV("pent_" + g_sim[i], 0);
      g_sigma[i] = CargarGV("sig_" + g_sim[i], 0);
      g_senal[i] = (int)CargarGV("sen_" + g_sim[i], 0);
     }
   NuevoDiaSiToca();
   EventSetTimer(60);   // los símbolos cripto pueden no tener ticks en el del gráfico
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { EventKillTimer(); }
void OnTick()  { Paso(); }
void OnTimer() { Paso(); }

//+------------------------------------------------------------------+
void Paso()
  {
   NuevoDiaSiToca();
   if(!ComprobarLimites()) return;
   ReintentarPendientes();
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   // lunes de esta semana (si el EA no estuvo en marcha el lunes, rebalancea en cuanto arranque)
   datetime hoy = TimeCurrent() - (TimeCurrent() % 86400);
   int dias = (t.day_of_week - InpDiaRebalanceo + 7) % 7;
   datetime lunes = hoy - dias * 86400;
   if(dias == 0 && t.hour < InpHoraRebalanceo) return;
   if((datetime)CargarGV("ultimo_rebalanceo", 0) == lunes) return;
   if(dias > 0) PrintFormat("Rebalanceo de la semana del %s hecho con %d días de retraso", TimeToString(lunes, TIME_DATE), dias);
   if(Rebalancear(lunes)) GuardarGV("ultimo_rebalanceo", (double)lunes);
  }

//+------------------------------------------------------------------+
//| Cierre D1 del día natural d (servidor); 0 si no hay barra de ese  |
//| día o anterior en los 3 días previos.                             |
//+------------------------------------------------------------------+
double CierreEn(string s, datetime d)
  {
   int sh = iBarShift(s, PERIOD_D1, d, false);   // barra que contiene d o la anterior
   if(sh < 0) return 0;
   datetime tb = iTime(s, PERIOD_D1, sh);
   if(tb > d || d - tb > 3 * 86400) return 0;
   return iClose(s, PERIOD_D1, sh);
  }

//+------------------------------------------------------------------+
//| Sigma semanal: desv. de los rendimientos log de los InpVolDias    |
//| días naturales previos (cierres por día natural, rellenando hacia |
//| delante como en Python), por raíz(7).                             |
//+------------------------------------------------------------------+
double SigmaSemanal(string s, datetime dom)
  {
   double r[]; ArrayResize(r, InpVolDias);
   int n = 0;
   double prev = CierreEn(s, dom - InpVolDias * 86400);
   if(prev <= 0) return 0;
   for(int k = InpVolDias - 1; k >= 0; k--)
     {
      double c = CierreEn(s, dom - k * 86400);
      if(c <= 0) return 0;
      r[n++] = MathLog(c / prev);
      prev = c;
     }
   if(n < 25) return 0;
   double m = 0; for(int i = 0; i < n; i++) m += r[i]; m /= n;
   double v = 0; for(int i = 0; i < n; i++) v += (r[i] - m) * (r[i] - m);
   v /= (n - 1);
   return MathSqrt(v) * MathSqrt(7.0);
  }

//+------------------------------------------------------------------+
bool Rebalancear(datetime lunes)
  {
   datetime dom = lunes - 86400;           // barra D1 del domingo (ya cerrada)
   int m = ArraySize(g_sim);
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   double objetivo[]; ArrayResize(objetivo, m); ArrayInitialize(objetivo, 0);
   double sig[]; ArrayResize(sig, m);
   double cierreDom[]; ArrayResize(cierreDom, m);
   int sen[]; ArrayResize(sen, m);
   double nocTotal = 0;
   bool datosOk = true;
   for(int i = 0; i < m; i++)
     {
      string s = g_sim[i];
      double c0 = CierreEn(s, dom), cL = CierreEn(s, dom - InpLookbackDias * 86400);
      cierreDom[i] = c0;
      sig[i] = SigmaSemanal(s, dom);
      if(!SeriesInfoInteger(s, PERIOD_D1, SERIES_SYNCHRONIZED)) { datosOk = false; PrintFormat("%s: historia D1 sincronizándose, se reintenta", s); continue; }
      datetime primera = (datetime)SeriesInfoInteger(s, PERIOD_D1, SERIES_FIRSTDATE);
      if(c0 <= 0 || cL <= 0 || sig[i] <= 0 || primera <= 0 || dom - primera < InpMinHistoriaDias * 86400)
        {
         sen[i] = 0;
         PrintFormat("%s: sin datos suficientes el %s (c0 %.5f, c28 %.5f, sigma %.4f): fuera",
                     s, TimeToString(dom, TIME_DATE), c0, cL, sig[i]);
         continue;
        }
      sen[i] = (c0 / cL - 1 > 0) ? 1 : 0;
      if(sen[i] == 1)
        {
         // pérdida por lote si el precio cae 1 sigma desde el cierre del domingo
         double perdida1 = 0;
         if(!OrderCalcProfit(ORDER_TYPE_BUY, s, 1.0, c0, c0 * (1 - sig[i]), perdida1) || perdida1 >= 0)
           { PrintFormat("%s: OrderCalcProfit falló (%d): fuera esta semana", s, GetLastError()); sen[i] = 0; continue; }
         objetivo[i] = (bal * InpRiesgoPct / 100.0) / -perdida1;
         double nocLote = 0;   // nocional de 1 lote en divisa de la cuenta
         if(!OrderCalcProfit(ORDER_TYPE_BUY, s, 1.0, c0, c0 * 2, nocLote)) nocLote = c0 * SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE);
         nocTotal += objetivo[i] * MathAbs(nocLote);
        }
     }
   if(!datosOk) return false;
   double escala = 1.0;
   if(bal > 0 && nocTotal / bal * 100.0 > InpExposicionMaxPct)
     {
      escala = InpExposicionMaxPct / (nocTotal / bal * 100.0);
      PrintFormat("Tope de exposición: nocional %.0f %% del balance → escala %.2f", nocTotal / bal * 100.0, escala);
     }
   for(int i = 0; i < m; i++)
     {
      string s = g_sim[i];
      // R de modelo de la semana que termina (misma definición que Python: N·ret, N = 1/sigma)
      if(InpRegistrarCSV && g_senal[i] == 1 && g_pEnt[i] > 0 && g_sigma[i] > 0 && cierreDom[i] > 0)   // g_senal = señal pura de la semana anterior
         EscribirSemana(dom, s, (cierreDom[i] / g_pEnt[i] - 1) / g_sigma[i], g_pEnt[i], cierreDom[i], g_sigma[i]);
      double paso = SymbolInfoDouble(s, SYMBOL_VOLUME_STEP), minL = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN),
             maxL = SymbolInfoDouble(s, SYMBOL_VOLUME_MAX);
      if(paso <= 0) { PrintFormat("%s: paso de volumen 0 (sin sincronizar): sin cambios esta vez", s); datosOk = false; continue; }
      double obj = MathFloor(objetivo[i] * escala / paso + 1e-9) * paso;
      if(obj < minL) obj = 0;
      obj = MathMin(obj, maxL);
      if(sen[i] == 1 && obj == 0)
         PrintFormat("%s: objetivo %.4f lotes < mínimo %.4f: fuera (balance pequeño para este riesgo)", s, objetivo[i] * escala, minL);
      g_obj[i] = obj;
      g_pend[i] = !AjustarVolumen(s, obj, paso);
      g_senal[i] = sen[i];   // el CSV de R de modelo sigue la señal, no la ejecución (comparable con Python)
      g_pEnt[i] = cierreDom[i]; g_sigma[i] = sig[i];
      GuardarGV("pent_" + s, g_pEnt[i]); GuardarGV("sig_" + s, g_sigma[i]); GuardarGV("sen_" + s, g_senal[i]);
      if(InpRegistrarCSV) EscribirRebalanceo(dom, s, sen[i], cierreDom[i], sig[i], obj);
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Lleva el volumen neto comprado del símbolo a `obj` lotes          |
//+------------------------------------------------------------------+
void ReintentarPendientes()
  {
   static datetime ultimo = 0;
   if(TimeCurrent() - ultimo < 60) return;
   ultimo = TimeCurrent();
   for(int i = 0; i < ArraySize(g_sim); i++)
      if(g_pend[i] && SymbolInfoDouble(g_sim[i], SYMBOL_VOLUME_STEP) > 0)
         g_pend[i] = !AjustarVolumen(g_sim[i], g_obj[i], SymbolInfoDouble(g_sim[i], SYMBOL_VOLUME_STEP));
  }

bool AjustarVolumen(string s, double obj, double paso)
  {
   double actual = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk != 0 && PositionGetString(POSITION_SYMBOL) == s && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         actual += PositionGetDouble(POSITION_VOLUME);
     }
   double dif = obj - actual;
   if(MathAbs(dif) < paso / 2) return true;
   double minL = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN);
   if(obj > 0 && MathAbs(dif) < minL - 1e-9) return true;   // ajuste menor que el lote mínimo: se deja como está
   trade.SetTypeFillingBySymbol(s);
   bool neteo = AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
   if(dif < 0 && neteo)
     {
      double v = NormalizeDouble(MathRound(-dif / paso) * paso, 8);
      if(trade.Sell(v, s, 0, 0, 0, "tendencia cripto reduce") && trade.ResultRetcode() == TRADE_RETCODE_DONE) return true;
      PrintFormat("%s: venta de %.4f falló (%d): se reintenta cada minuto", s, v, trade.ResultRetcode());
      return false;
     }
   if(dif > 0)
     {
      dif = MathRound(dif / paso) * paso;
      if(trade.Buy(NormalizeDouble(dif, 8), s, 0, 0, 0, "tendencia cripto") && trade.ResultRetcode() == TRADE_RETCODE_DONE)
         return true;
      PrintFormat("%s: compra de %.4f falló (%d): se reintenta cada minuto", s, dif, trade.ResultRetcode());
      return false;
     }
   double quitar = -dif;   // cerrar de las posiciones más recientes hacia atrás
   for(int i = PositionsTotal() - 1; i >= 0 && quitar >= paso / 2; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetString(POSITION_SYMBOL) != s || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      double v = PositionGetDouble(POSITION_VOLUME);
      double parte = NormalizeDouble(MathRound(quitar / paso) * paso, 8);
      bool total = (v <= parte + paso / 2) || (v - parte < minL - 1e-9);   // no dejar un resto por debajo del mínimo
      bool ok = total ? trade.PositionClose(tk) : trade.PositionClosePartial(tk, parte);
      if(!ok) { PrintFormat("%s: cierre de %I64u falló (%d): se reintenta cada minuto", s, tk, trade.ResultRetcode()); return false; }
      quitar -= total ? v : parte;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Día de servidor, base diaria y límites (como la plantilla)        |
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
     }
   else
     {
      g_baseDia = MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY));
      g_paradoDia = false;
      GuardarGV("dia", (double)dia);
      GuardarGV("base_dia", g_baseDia);
      GuardarGV("parado_dia", 0);
     }
  }

bool ComprobarLimites()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!g_paradoTotal && eq <= g_inicial * (1 - InpPerdidaTotalPct / 100.0))
     { g_paradoTotal = true; GuardarGV("parado_total", 1); Avisar("Corte TOTAL alcanzado: EA parado hasta revisión manual"); }
   if(!g_paradoTotal && InpObjetivoPct > 0 && eq >= g_inicial * (1 + InpObjetivoPct / 100.0))
     { g_paradoTotal = true; GuardarGV("parado_total", 1); Avisar("Objetivo del reto alcanzado: EA parado"); }
   if(!g_paradoDia && eq <= g_baseDia - g_inicial * InpPerdidaDiariaPct / 100.0)
     { g_paradoDia = true; GuardarGV("parado_dia", 1); Avisar("Corte DIARIO alcanzado: todo cerrado hasta el próximo rebalanceo"); }
   if(g_paradoDia || g_paradoTotal)
     {
      CerrarTodo();
      // tras un corte diario se queda fuera hasta el lunes siguiente (marca la semana como hecha)
      for(int i = 0; i < ArraySize(g_sim); i++) { g_senal[i] = 0; g_pend[i] = false; g_obj[i] = 0; GuardarGV("sen_" + g_sim[i], 0); }
      return false;
     }
   return true;
  }

void CerrarTodo()
  {
   static datetime ultimo = 0;
   if(TimeCurrent() - ultimo < 1) return;
   ultimo = TimeCurrent();
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk != 0 && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         if(!trade.PositionClose(tk)) PrintFormat("No se pudo cerrar %I64u: %d", tk, trade.ResultRetcode());
     }
  }

void Avisar(string texto)
  {
   Print(texto);
   if(!MQLInfoInteger(MQL_TESTER)) { Alert(texto); SendNotification("TendenciaCripto: " + texto); }
  }

double CargarGV(string clave, double defecto)
  {
   string n = g_prefijo + clave;
   return GlobalVariableCheck(n) ? GlobalVariableGet(n) : defecto;
  }
void GuardarGV(string clave, double valor) { GlobalVariableSet(g_prefijo + clave, valor); }

//+------------------------------------------------------------------+
//| CSV en Common/Files                                               |
//|  TendenciaCripto_semanas.csv: R de modelo por símbolo y semana     |
//|  TendenciaCripto_rebalanceos.csv: señal, sigma y lotes objetivo    |
//|  TendenciaCripto_deals.csv: cada salida real con beneficio y swap  |
//+------------------------------------------------------------------+
void Fila(string nombre, string cab, string fila)
  {
   int f = FileOpen(nombre, FILE_READ | FILE_WRITE | FILE_TXT | FILE_COMMON | FILE_ANSI);
   if(f == INVALID_HANDLE) { PrintFormat("CSV %s: no se puede abrir (%d)", nombre, GetLastError()); return; }
   if(FileSize(f) == 0) FileWriteString(f, cab + "\n");
   FileSeek(f, 0, SEEK_END);
   FileWriteString(f, fila + "\n");
   FileClose(f);
  }

void EscribirSemana(datetime dom, string s, double r, double p0, double p1, double sg)
  {
   Fila("TendenciaCripto_semanas.csv", "fecha;simbolo;r_modelo;precio_ini;precio_fin;sigma",
        StringFormat("%s;%s;%.4f;%.8g;%.8g;%.6f", TimeToString(dom, TIME_DATE), s, r, p0, p1, sg));
  }

void EscribirRebalanceo(datetime dom, string s, int sen, double c0, double sg, double lotes)
  {
   Fila("TendenciaCripto_rebalanceos.csv", "domingo;simbolo;senal;cierre;sigma;lotes;balance",
        StringFormat("%s;%s;%d;%.8g;%.6f;%.4f;%.2f", TimeToString(dom, TIME_DATE), s, sen, c0, sg, lotes,
                     AccountInfoDouble(ACCOUNT_BALANCE)));
  }

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
  {
   if(!InpRegistrarCSV || trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;
   long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   Fila("TendenciaCripto_deals.csv", "hora;simbolo;entrada;volumen;precio;beneficio;comision;swap",
        StringFormat("%s;%s;%s;%.4f;%.8g;%.2f;%.2f;%.2f",
                     TimeToString((datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME), TIME_DATE | TIME_SECONDS),
                     HistoryDealGetString(trans.deal, DEAL_SYMBOL), entry == DEAL_ENTRY_IN ? "in" : "out",
                     HistoryDealGetDouble(trans.deal, DEAL_VOLUME), HistoryDealGetDouble(trans.deal, DEAL_PRICE),
                     HistoryDealGetDouble(trans.deal, DEAL_PROFIT), HistoryDealGetDouble(trans.deal, DEAL_COMMISSION),
                     HistoryDealGetDouble(trans.deal, DEAL_SWAP)));
  }
//+------------------------------------------------------------------+
