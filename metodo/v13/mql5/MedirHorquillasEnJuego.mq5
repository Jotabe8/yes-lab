//+------------------------------------------------------------------+
//| MedirHorquillasEnJuego.mq5 (script, solo LEE ticks)               |
//| Horquilla mediana y p90 (% del precio) en la 1.ª hora de la       |
//| apertura propia de los 5 mercados del ORB en juego (v13).         |
//| Salida: Common/Files/horquillas_en_juego.csv                      |
//+------------------------------------------------------------------+
#property script_show_inputs
input int InpDias = 60;            // días hábiles hacia atrás
input int InpServidorMasNY = 7;    // FTMO: servidor = Nueva York + 7 h

string SIM[]  = {"GER40.cash", "UK100.cash", "JP225.cash", "XAUUSD", "USOIL.cash"};
int    ZONA[] = {0, 1, 2, 3, 3};
int    AP[]   = {540, 480, 540, 500, 540};   // minutos locales de la apertura

datetime Domingo(int anio, int mes, int n)
  {
   MqlDateTime s; ZeroMemory(s); s.year = anio; s.mon = mes; s.day = 1;
   MqlDateTime x; TimeToStruct(StructToTime(s), x);
   int primero = 1 + (7 - x.day_of_week) % 7;
   if(n > 0) { s.day = primero + 7 * (n - 1); return StructToTime(s); }
   int dias = (mes == 2) ? 28 : ((mes == 4 || mes == 6 || mes == 9 || mes == 11) ? 30 : 31);
   int u = primero; while(u + 7 <= dias) u += 7; s.day = u; return StructToTime(s);
  }
bool VUSA(datetime u) { MqlDateTime t; TimeToStruct(u, t); return u >= Domingo(t.year, 3, 2) + 25200 && u < Domingo(t.year, 11, 1) + 21600; }
bool VUE(datetime u)  { MqlDateTime t; TimeToStruct(u, t); return u >= Domingo(t.year, 3, -1) + 3600 && u < Domingo(t.year, 10, -1) + 3600; }
int Desf(int z, datetime u) { if(z == 0) return VUE(u) ? 2 : 1; if(z == 1) return VUE(u) ? 1 : 0; if(z == 2) return 9; return VUSA(u) ? -4 : -5; }
datetime LocalAServidor(int z, datetime loc)
  {
   datetime u = loc - Desf(z, loc - 7200) * 3600; u = loc - Desf(z, u) * 3600;
   return u + ((VUSA(u) ? -4 : -5) + InpServidorMasNY) * 3600;
  }

void OnStart()
  {
   int f = FileOpen("horquillas_en_juego.csv", FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_ANSI, ';');
   FileWrite(f, "simbolo", "dias", "mediana_pct", "p90_pct", "mediana_puntos", "precio_medio");
   datetime hoy = TimeCurrent(); hoy -= hoy % 86400;
   for(int s = 0; s < ArraySize(SIM); s++)
     {
      if(!SymbolSelect(SIM[s], true)) { FileWrite(f, SIM[s], 0, "", "", "", ""); continue; }
      double pct[], pts[], px = 0; int nd = 0, n = 0;
      for(int d = 1; d < InpDias * 2 && nd < InpDias; d++)
        {
         datetime loc = hoy - d * 86400;
         MqlDateTime t; TimeToStruct(loc, t);
         if(t.day_of_week == 0 || t.day_of_week == 6) continue;
         datetime ini = LocalAServidor(ZONA[s], loc + AP[s] * 60);
         MqlTick tk[];
         int k = CopyTicksRange(SIM[s], tk, COPY_TICKS_INFO, (ulong)ini * 1000, (ulong)(ini + 3600) * 1000);
         if(k < 50) continue;
         nd++;
         for(int i = 0; i < k; i += MathMax(1, k / 400))
           {
            double m = (tk[i].ask + tk[i].bid) / 2; if(m <= 0) continue;
            ArrayResize(pct, n + 1); ArrayResize(pts, n + 1);
            pct[n] = 100 * (tk[i].ask - tk[i].bid) / m; pts[n] = tk[i].ask - tk[i].bid; px += m; n++;
           }
        }
      if(n == 0) { FileWrite(f, SIM[s], nd, "", "", "", ""); continue; }
      ArraySort(pct); ArraySort(pts);
      FileWrite(f, SIM[s], nd, DoubleToString(pct[n / 2], 5), DoubleToString(pct[(int)(n * 0.9)], 5),
                DoubleToString(pts[n / 2], 3), DoubleToString(px / n, 2));
     }
   FileClose(f);
   Print("Hecho: Common\\Files\\horquillas_en_juego.csv");
  }
