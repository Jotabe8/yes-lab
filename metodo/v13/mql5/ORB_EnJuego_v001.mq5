//+------------------------------------------------------------------+
//| ORB_EnJuego_v001.mq5                                             |
//| ORB "en juego" en la apertura propia del mercado del gráfico.     |
//| Regla validada en Python: metodo/v13/PREREGISTRO_ORB_EN_JUEGO.md  |
//| (variante V2 rango). Una instancia por gráfico/símbolo:           |
//|   GER40.cash  zona 0 (Fráncfort) 9:00, salida 17:25               |
//|   UK100.cash  zona 1 (Londres)   8:00, salida 16:25               |
//|   JP225.cash  zona 2 (Tokio)     9:00, salida 15:25 (14:55 <2024-11-05) |
//|   XAUUSD      zona 3 (Nueva York) 8:20, salida 13:25              |
//|   USOIL.cash  zona 3 (Nueva York) 9:00, salida 14:25              |
//| Hora del servidor FTMO = Nueva York + 7 h (InpServidorMasNY).     |
//| NO usar en la cuenta real del v018 hasta pasar P5-P6.             |
//+------------------------------------------------------------------+
#property copyright "yes-lab"
#property version   "1.01"

#include <Trade/Trade.mqh>

//--- Mercado (hora LOCAL del mercado)
input int    InpZona             = 0;      // 0 Fráncfort, 1 Londres, 2 Tokio, 3 Nueva York
input int    InpAperturaHora     = 9;
input int    InpAperturaMin      = 0;
input int    InpSalidaHora       = 17;
input int    InpSalidaMin        = 25;
input bool   InpJP225Salida1525  = false;  // true en JP225: salida 15:25 desde 2024-11-05 (antes 14:55)
input int    InpServidorMasNY    = 7;      // horas que el servidor va por delante de Nueva York (FTMO: 7)
//--- Regla (no tocar: es la validada)
input int    InpRangoMin         = 10;     // minutos del rango de apertura
input double InpCuerpoMin        = 0.10;   // cuerpo mínimo / rango
input double InpStopATR          = 0.15;   // stop = x · ATR(14) de la sesión
input double InpUmbralRango      = 1.5;    // en juego si rango / media 14 días >= umbral
input int    InpDiasMedia        = 14;
//--- Riesgo
input double InpRiesgoPct        = 0.30;   // Riesgo por operación (% del balance)
input double InpLotesFijos       = 0.0;    // >0: lotes fijos (ignora el riesgo)
//--- Límites de la cuenta (por debajo de los de FTMO, con margen por huecos)
input double InpPerdidaDiariaPct = 4.0;
input double InpPerdidaTotalPct  = 8.0;
input double InpBalanceInicial   = 0.0;    // 0 = el actual al arrancar
input double InpObjetivoPct      = 0.0;
input long   InpMagic            = 261301; // uno distinto por símbolo
input bool   InpRegistrarCSV     = true;

CTrade trade;
string g_prefijo;
datetime g_dia = 0;
double g_baseDia = 0;
bool   g_paradoDia = false;
bool   g_paradoTotal = false;
int    g_opsHoy = 0;
double g_inicial = 0;
datetime g_diaLocalHecho = 0;   // fecha local del mercado ya evaluada (una señal al día)

//+------------------------------------------------------------------+
//| Husos horarios                                                    |
//+------------------------------------------------------------------+
datetime Domingo(int anio, int mes, int n)   // n-ésimo domingo (n = -1: el último)
  {
   MqlDateTime s; ZeroMemory(s); s.year = anio; s.mon = mes; s.day = 1;
   datetime d = StructToTime(s);
   MqlDateTime x; TimeToStruct(d, x);
   int primero = 1 + (7 - x.day_of_week) % 7;
   if(n > 0) { s.day = primero + 7 * (n - 1); return StructToTime(s); }
   int dias = (mes == 2) ? 28 : ((mes == 4 || mes == 6 || mes == 9 || mes == 11) ? 30 : 31);
   int u = primero; while(u + 7 <= dias) u += 7;
   s.day = u; return StructToTime(s);
  }
bool VeranoUSA(datetime utc)
  {
   MqlDateTime t; TimeToStruct(utc, t);
   datetime ini = Domingo(t.year, 3, 2) + 7 * 3600, fin = Domingo(t.year, 11, 1) + 6 * 3600;
   return utc >= ini && utc < fin;
  }
bool VeranoUE(datetime utc)
  {
   MqlDateTime t; TimeToStruct(utc, t);
   datetime ini = Domingo(t.year, 3, -1) + 3600, fin = Domingo(t.year, 10, -1) + 3600;
   return utc >= ini && utc < fin;
  }
int DesfaseNY(datetime utc) { return VeranoUSA(utc) ? -4 : -5; }
int DesfaseZona(datetime utc)
  {
   if(InpZona == 0) return VeranoUE(utc) ? 2 : 1;
   if(InpZona == 1) return VeranoUE(utc) ? 1 : 0;
   if(InpZona == 2) return 9;
   return DesfaseNY(utc);
  }
datetime ServidorAUtc(datetime srv)
  {
   datetime g = srv - 3 * 3600;                       // verano de EE. UU.: NY = UTC-4
   if(VeranoUSA(g)) return g;
   return srv - 2 * 3600;                             // invierno: NY = UTC-5
  }
datetime UtcAServidor(datetime utc) { return utc + (DesfaseNY(utc) + InpServidorMasNY) * 3600; }
datetime LocalAServidor(datetime local)
  {
   datetime utc = local - DesfaseZona(local - 3600 * 2) * 3600;
   utc = local - DesfaseZona(utc) * 3600;
   return UtcAServidor(utc);
  }
datetime DiaLocalDe(datetime srv)
  {
   datetime utc = ServidorAUtc(srv);
   datetime loc = utc + DesfaseZona(utc) * 3600;
   return loc - (loc % 86400);
  }
int SalidaMinutos(datetime diaLocal)
  {
   if(InpJP225Salida1525)
     {
      MqlDateTime c; ZeroMemory(c); c.year = 2024; c.mon = 11; c.day = 5;
      return diaLocal < StructToTime(c) ? 14 * 60 + 55 : 15 * 60 + 25;
     }
   return InpSalidaHora * 60 + InpSalidaMin;
  }

//+------------------------------------------------------------------+
//| Datos de una sesión (en M1)                                       |
//+------------------------------------------------------------------+
bool Sesion(datetime diaLocal, double &h, double &l, double &c, double &rh, double &rl, double &ro, double &rc, int &nr)
  {
   int a0 = InpAperturaHora * 60 + InpAperturaMin;
   datetime ini = LocalAServidor(diaLocal + a0 * 60);
   datetime fin = LocalAServidor(diaLocal + SalidaMinutos(diaLocal) * 60);
   datetime finR = LocalAServidor(diaLocal + (a0 + InpRangoMin) * 60);
   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, ini, fin - 1, r);
   if(n < 60) return false;
   h = -DBL_MAX; l = DBL_MAX; rh = -DBL_MAX; rl = DBL_MAX; nr = 0; ro = 0; rc = 0;
   for(int i = 0; i < n; i++)
     {
      h = MathMax(h, r[i].high); l = MathMin(l, r[i].low);
      if(r[i].time < finR)
        {
         if(nr == 0) ro = r[i].open;
         rc = r[i].close; rh = MathMax(rh, r[i].high); rl = MathMin(rl, r[i].low); nr++;
        }
     }
   c = r[n - 1].close;
   return nr >= 7;
  }

// ATR(14) de sesión y media del rango de apertura de los días válidos anteriores
bool Historia(datetime hoyLocal, double &atr, double &mediaRango)
  {
   double H[], L[], C[], R[];
   int k = 0;
   ArrayResize(H, InpDiasMedia + 1); ArrayResize(L, InpDiasMedia + 1); ArrayResize(C, InpDiasMedia + 1); ArrayResize(R, InpDiasMedia + 1);
   for(int d = 1; d <= 60 && k < InpDiasMedia + 1; d++)
     {
      datetime dl = hoyLocal - d * 86400;
      MqlDateTime t; TimeToStruct(dl, t);
      if(t.day_of_week == 0 || t.day_of_week == 6) continue;
      double h, l, c, rh, rl, ro, rc; int nr;
      if(!Sesion(dl, h, l, c, rh, rl, ro, rc, nr)) continue;
      H[k] = h; L[k] = l; C[k] = c; R[k] = rh - rl; k++;          // k = 0 es el día más reciente
     }
   if(k < InpDiasMedia + 1) return false;
   double sTR = 0, sR = 0;
   for(int i = 0; i < InpDiasMedia; i++)
     {
      double pc = C[i + 1];
      sTR += MathMax(H[i] - L[i], MathMax(MathAbs(H[i] - pc), MathAbs(L[i] - pc)));
      sR  += R[i];
     }
   atr = sTR / InpDiasMedia; mediaRango = sR / InpDiasMedia;
   return atr > 0 && mediaRango > 0;
  }

//+------------------------------------------------------------------+
//| Señal: +1/-1 una vez al día al cerrar el rango; sl en precio      |
//+------------------------------------------------------------------+
int Senal(double &sl, string &nota)
  {
   datetime ahora = TimeCurrent();
   datetime hoy = DiaLocalDe(ahora);
   if(hoy == g_diaLocalHecho) return 0;
   MqlDateTime t; TimeToStruct(hoy, t);
   if(t.day_of_week == 0 || t.day_of_week == 6) return 0;
   int a0 = InpAperturaHora * 60 + InpAperturaMin;
   datetime finR = LocalAServidor(hoy + (a0 + InpRangoMin) * 60);
   datetime salida = LocalAServidor(hoy + SalidaMinutos(hoy) * 60);
   if(ahora < finR) return 0;
   g_diaLocalHecho = hoy;                    // pase lo que pase, hoy ya no se evalúa más
   if(ahora >= finR + 120 || ahora >= salida - 600) { nota = "tarde"; return 0; }
   // rango de hoy
   datetime ini = LocalAServidor(hoy + a0 * 60);
   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, ini, finR - 1, r);
   if(n < 7) { nota = "rango incompleto"; return 0; }
   double O = r[0].open, C = r[n - 1].close, H = -DBL_MAX, L = DBL_MAX;
   for(int i = 0; i < n; i++) { H = MathMax(H, r[i].high); L = MathMin(L, r[i].low); }
   if(H - L <= 0 || MathAbs(C - O) < InpCuerpoMin * (H - L)) { nota = "cuerpo pequeño"; return 0; }
   double atr, media;
   if(!Historia(hoy, atr, media)) { nota = "sin historia"; return 0; }
   double rr = (H - L) / media;
   nota = StringFormat("rrango %.2f atr %.2f", rr, atr);
   if(rr < InpUmbralRango) return 0;
   int dir = C > O ? 1 : -1;
   double p = dir > 0 ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   sl = NormalizeDouble(p - dir * InpStopATR * atr, _Digits);
   return dir;
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   g_prefijo = StringFormat("oej_%I64d_%I64d_%s_", AccountInfoInteger(ACCOUNT_LOGIN), InpMagic, _Symbol);
   g_inicial = InpBalanceInicial > 0 ? InpBalanceInicial : CargarGV("inicial", AccountInfoDouble(ACCOUNT_BALANCE));
   GuardarGV("inicial", g_inicial);
   g_paradoTotal = CargarGV("parado_total", 0) > 0;
   g_diaLocalHecho = (datetime)CargarGV("dia_local_hecho", 0);
   NuevoDiaSiToca();
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   NuevoDiaSiToca();
   if(!ComprobarLimites()) return;
   datetime ahora = TimeCurrent();
   datetime hoy = DiaLocalDe(ahora);
   datetime salida = LocalAServidor(hoy + SalidaMinutos(hoy) * 60);
   ulong ticket = PosicionPropia();
   if(ticket != 0)
     {
      datetime abierta = (datetime)PositionGetInteger(POSITION_TIME);
      if(ahora >= salida || DiaLocalDe(abierta) != hoy) CerrarTodo("salida horaria");
      return;
     }
   double sl; string nota = "";
   int dir = Senal(sl, nota);
   if(nota != "") { PrintFormat("%s %s: %s", _Symbol, TimeToString(hoy, TIME_DATE), nota); GuardarGV("dia_local_hecho", (double)g_diaLocalHecho); }
   if(dir == 0) return;
   double precio = dir > 0 ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double lotes = Lotes(dir, precio, sl);
   if(lotes <= 0) { Print("Lotes = 0 (stop demasiado ancho para el riesgo)"); return; }
   bool ok = dir > 0 ? trade.Buy(lotes, _Symbol, 0, sl, 0, "ORB en juego")
                     : trade.Sell(lotes, _Symbol, 0, sl, 0, "ORB en juego");
   if(ok && trade.ResultRetcode() == TRADE_RETCODE_DONE) { g_opsHoy++; GuardarGV("ops_hoy", g_opsHoy); }
   else PrintFormat("Orden rechazada: %d", trade.ResultRetcode());
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
   // Datos de la salida antes de HistorySelectByPosition (cambia la selección del historial)
   datetime cierre = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
   long     pos    = HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   bool     largo  = HistoryDealGetInteger(trans.deal, DEAL_TYPE) == DEAL_TYPE_SELL;
   double   vol    = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
   double   precio = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double   benef  = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);
   double   comi   = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
   double   swap   = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
   // Entrada de la misma posición: hora, precio y stop inicial, para calcular R igual que Python
   // (metodo/comparar_ops.py empareja operación a operación con esto)
   datetime apertura = 0;
   double   p_ent = 0, sl_ini = 0;
   if(HistorySelectByPosition(pos))
      for(int i = 0; i < HistoryDealsTotal(); i++)
        {
         ulong d = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(d, DEAL_ENTRY) != DEAL_ENTRY_IN) continue;
         apertura = (datetime)HistoryDealGetInteger(d, DEAL_TIME);
         p_ent    = HistoryDealGetDouble(d, DEAL_PRICE);
         sl_ini   = HistoryDealGetDouble(d, DEAL_SL);
         break;
        }
   double riesgo = (sl_ini > 0 && p_ent > 0) ? MathAbs(p_ent - sl_ini) : 0;
   double r = (riesgo > 0) ? (largo ? precio - p_ent : p_ent - precio) / riesgo : 0;
   if(riesgo <= 0) PrintFormat("CSV: posición %I64d sin stop en la entrada, r_bruto = 0", pos);
   string nombre = MQLInfoString(MQL_PROGRAM_NAME) + "_" + _Symbol + "_ops.csv";
   int f = FileOpen(nombre, FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ';');
   if(f == INVALID_HANDLE) return;
   // Columnas nuevas al final (14-11-2026): borra un CSV antiguo antes de un backtest nuevo
   if(FileSize(f) == 0) FileWrite(f, "cierre", "posicion", "tipo", "volumen", "precio", "beneficio", "comision", "swap",
                                  "apertura", "precio_entrada", "sl_inicial", "r_bruto");
   FileSeek(f, 0, SEEK_END);
   FileWrite(f, TimeToString(cierre, TIME_DATE | TIME_SECONDS), pos, largo ? "cierra_largo" : "cierra_corto",
             vol, precio, benef, comi, swap,
             TimeToString(apertura, TIME_DATE | TIME_SECONDS), DoubleToString(p_ent, _Digits),
             DoubleToString(sl_ini, _Digits), DoubleToString(r, 3));
   FileClose(f);
  }
//+------------------------------------------------------------------+
