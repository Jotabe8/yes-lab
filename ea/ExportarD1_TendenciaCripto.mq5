//+------------------------------------------------------------------+
//| ExportarD1_TendenciaCripto.mq5 (script)                           |
//| Exporta a Common/Files/TC_D1/<SIMBOLO>.csv las velas D1 de los     |
//| símbolos cripto y un resumen de sus especificaciones (swap,        |
//| horquilla, contrato, sesiones) en TC_D1/_especificaciones.csv.      |
//+------------------------------------------------------------------+
#property script_show_inputs
input string InpSimbolos = "BTCUSD,ETHUSD,LTCUSD,XRPUSD,BCHUSD,ADAUSD,DOGEUSD,DOTUSD,SOLUSD,AVAXUSD,LNKUSD,XLMUSD,ETCUSD,BNBUSD,UNIUSD,TRXUSD,NEARUSD,ATOMUSD,FILUSD,EOSUSD";
input bool   InpTodosCripto = true;   // además, todos los símbolos del bróker cuya ruta contenga "Crypto"

void Exportar(string s, int fe)
  {
   MqlRates r[];
   int n = CopyRates(s, PERIOD_D1, 0, 5000, r);
   if(n <= 0) { PrintFormat("%s: sin velas D1 (%d)", s, GetLastError()); return; }
   int f = FileOpen("TC_D1\\" + s + ".csv", FILE_WRITE | FILE_TXT | FILE_COMMON | FILE_ANSI);
   if(f == INVALID_HANDLE) return;
   FileWriteString(f, "time;open;high;low;close;spread\n");
   for(int i = 0; i < n; i++)
      FileWriteString(f, StringFormat("%s;%.8g;%.8g;%.8g;%.8g;%d\n", TimeToString(r[i].time, TIME_DATE),
                                      r[i].open, r[i].high, r[i].low, r[i].close, r[i].spread));
   FileClose(f);
   double bid = SymbolInfoDouble(s, SYMBOL_BID), ask = SymbolInfoDouble(s, SYMBOL_ASK);
   FileWriteString(fe, StringFormat("%s;%s;%d;%s;%.6f;%.6f;%d;%.4f;%.4f;%.4f;%.4f;%.6f;%.6f;%d;%.8g;%.8g\n", s,
                   SymbolInfoString(s, SYMBOL_PATH), n, TimeToString(r[0].time, TIME_DATE),
                   SymbolInfoDouble(s, SYMBOL_SWAP_LONG), SymbolInfoDouble(s, SYMBOL_SWAP_SHORT),
                   (int)SymbolInfoInteger(s, SYMBOL_SWAP_MODE), SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE),
                   SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), SymbolInfoDouble(s, SYMBOL_VOLUME_STEP),
                   SymbolInfoDouble(s, SYMBOL_MARGIN_INITIAL), bid, ask, (int)SymbolInfoInteger(s, SYMBOL_SWAP_ROLLOVER3DAYS),
                   (bid > 0 ? (ask - bid) / bid * 100 : 0), SymbolInfoDouble(s, SYMBOL_POINT)));
  }

void OnStart()
  {
   int fe = FileOpen("TC_D1\\_especificaciones.csv", FILE_WRITE | FILE_TXT | FILE_COMMON | FILE_ANSI);
   FileWriteString(fe, "simbolo;ruta;velas_d1;primera;swap_largo;swap_corto;modo_swap;contrato;vol_min;vol_paso;margen_ini;bid;ask;dia_swap_triple;horquilla_pct;punto\n");
   string hechos = ",";
   string partes[]; int n = StringSplit(InpSimbolos, ',', partes);
   for(int i = 0; i < n; i++)
      if(SymbolSelect(partes[i], true)) { Exportar(partes[i], fe); hechos += partes[i] + ","; }
      else PrintFormat("%s no existe", partes[i]);
   if(InpTodosCripto)
      for(int i = 0; i < SymbolsTotal(false); i++)
        {
         string s = SymbolName(i, false);
         if(StringFind(SymbolInfoString(s, SYMBOL_PATH), "Crypto") < 0 && StringFind(SymbolInfoString(s, SYMBOL_PATH), "crypto") < 0) continue;
         if(StringFind(hechos, "," + s + ",") >= 0) continue;
         SymbolSelect(s, true); Exportar(s, fe); hechos += s + ",";
        }
   FileClose(fe);
   Print("Exportado a Common/Files/TC_D1: ", hechos);
  }
