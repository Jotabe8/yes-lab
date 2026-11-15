//+------------------------------------------------------------------+
//| MedirCosteGotobi.mq5  (script, solo LEE ticks; no opera)          |
//| Mide la horquilla real de USDJPY en el bróker a la hora del       |
//| gotobi: entrada 08:00-08:05 JST (23:00 UTC) y salida 09:50-09:55  |
//| JST (00:50 UTC). Coste ida y vuelta = media de las dos horquillas |
//| + comisión. Escribe Common\Files\coste_gotobi_<cuenta>.csv        |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSimbolo      = "USDJPY";  // símbolo del bróker
input int    InpMeses        = 6;         // meses hacia atrás
input double InpComisionRT   = 5.0;       // comisión ida y vuelta, USD por lote de 100.000
input double InpUmbralPips   = 0.8;       // coste total máximo para reabrir el gotobi

// --- horario de verano de EE. UU. (el servidor FTMO va a NY+7) ---
datetime NthDomingo(int y,int mes,int n)
  {
   MqlDateTime t; ZeroMemory(t); t.year=y; t.mon=mes; t.day=1;
   datetime d=StructToTime(t); TimeToStruct(d,t);
   int primero=(7-t.day_of_week)%7;              // días hasta el primer domingo
   return d+(primero+7*(n-1))*86400;
  }
bool VeranoUS(datetime utc)
  {
   MqlDateTime t; TimeToStruct(utc,t);
   datetime ini=NthDomingo(t.year,3,2)+7*3600;   // 2º domingo de marzo, 02:00 NY = 07:00 UTC
   datetime fin=NthDomingo(t.year,11,1)+6*3600;  // 1er domingo de noviembre, 02:00 NY = 06:00 UTC
   return utc>=ini && utc<fin;
  }
datetime UtcAServidor(datetime utc) { return utc+(VeranoUS(utc)?3:2)*3600; }

// --- días gotobi: 5,10,15,20,25 y último del mes; fin de semana -> viernes anterior ---
bool EsGotobi(datetime dia)   // dia = fecha JST a las 00:00
  {
   MqlDateTime t; TimeToStruct(dia,t);
   int y=t.year, m=t.mon;
   int dias[]={31,28,31,30,31,30,31,31,30,31,30,31};
   int ult=dias[m-1]; if(m==2 && ((y%4==0 && y%100!=0) || y%400==0)) ult=29;
   int cand[6]={5,10,15,20,25,0}; cand[5]=ult;
   for(int i=0;i<6;i++)
     {
      MqlDateTime c; ZeroMemory(c); c.year=y; c.mon=m; c.day=cand[i];
      datetime g=StructToTime(c); TimeToStruct(g,c);
      while(c.day_of_week==0 || c.day_of_week==6) { g-=86400; TimeToStruct(g,c); }
      if(g==dia) return true;
     }
   return false;
  }

// horquilla mediana (en precio) de los ticks de [desde, desde+5 min) en hora del servidor
bool Horquilla(datetime desde_srv,double &mediana,int &n)
  {
   MqlTick tk[];
   ulong a=(ulong)desde_srv*1000, b=(ulong)(desde_srv+300)*1000;
   n=CopyTicksRange(InpSimbolo,tk,COPY_TICKS_INFO,a,b);
   if(n<=0) return false;
   double s[]; ArrayResize(s,n);
   for(int i=0;i<n;i++) s[i]=tk[i].ask-tk[i].bid;
   ArraySort(s);
   mediana=(n%2==1)?s[n/2]:(s[n/2-1]+s[n/2])/2.0;
   return true;
  }

double Mediana(double &v[])
  {
   int n=ArraySize(v); if(n==0) return 0;
   double c[]; ArrayCopy(c,v); ArraySort(c);
   return (n%2==1)?c[n/2]:(c[n/2-1]+c[n/2])/2.0;
  }

void OnStart()
  {
   if(!SymbolSelect(InpSimbolo,true)) { Print("No existe el símbolo ",InpSimbolo); return; }
   double pip=(SymbolInfoInteger(InpSimbolo,SYMBOL_DIGITS)>=3)?0.01:0.0001;
   string fn="coste_gotobi_"+IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN))+".csv";
   int h=FileOpen(fn,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';');
   if(h==INVALID_HANDLE) { Print("No se pudo crear ",fn); return; }
   FileWrite(h,"fecha_jst","gotobi","horq_entrada_pips","horq_salida_pips","ticks_entrada","ticks_salida","comision_pips","coste_total_pips");

   datetime hoy=TimeGMT(); hoy-=hoy%86400;
   datetime ini=hoy-InpMeses*31*86400;
   double todos[], gotobis[], ent_v[], sal_v[];
   int dias=0;
   for(datetime d=ini; d<=hoy; d+=86400)          // d = fecha JST (00:00)
     {
      MqlDateTime t; TimeToStruct(d,t);
      if(t.day_of_week==0 || t.day_of_week==6) continue;
      datetime ent_utc=d-3600;                     // 08:00 JST = 23:00 UTC del día anterior
      datetime sal_utc=d+50*60;                    // 09:50 JST = 00:50 UTC
      double se,ss; int ne,ns;
      if(!Horquilla(UtcAServidor(ent_utc),se,ne)) continue;
      if(!Horquilla(UtcAServidor(sal_utc),ss,ns)) continue;
      double precio=SymbolInfoDouble(InpSimbolo,SYMBOL_BID);
      MqlTick tk[]; if(CopyTicksRange(InpSimbolo,tk,COPY_TICKS_INFO,(ulong)UtcAServidor(ent_utc)*1000,(ulong)(UtcAServidor(ent_utc)+300)*1000)>0) precio=tk[0].bid;
      double com=InpComisionRT*precio/1000.0;     // USD por lote -> pips de USDJPY
      double total=(se+ss)/2.0/pip+com;
      bool g=EsGotobi(d);
      FileWrite(h,TimeToString(d,TIME_DATE),g?1:0,DoubleToString(se/pip,2),DoubleToString(ss/pip,2),ne,ns,DoubleToString(com,2),DoubleToString(total,2));
      int k=ArraySize(todos); ArrayResize(todos,k+1); todos[k]=total;
      ArrayResize(ent_v,k+1); ent_v[k]=se/pip; ArrayResize(sal_v,k+1); sal_v[k]=ss/pip;
      if(g) { int j=ArraySize(gotobis); ArrayResize(gotobis,j+1); gotobis[j]=total; }
      dias++;
     }
   FileClose(h);
   if(dias==0) { Print("Sin ticks en el periodo: abre un gráfico M1 de ",InpSimbolo," y baja el historial, o prueba con menos meses"); return; }
   double mt=Mediana(todos), mg=Mediana(gotobis);
   string res=StringFormat("GOTOBI coste real %s | días %d (gotobi %d) | horquilla mediana entrada %.2f pips, salida %.2f | coste total mediano %.2f pips (días gotobi %.2f) | umbral %.2f -> %s",
                           InpSimbolo,dias,ArraySize(gotobis),Mediana(ent_v),Mediana(sal_v),mt,mg,InpUmbralPips,
                           (mg<=InpUmbralPips)?"POR DEBAJO: vale la pena seguir":"POR ENCIMA: el gotobi sigue sin pagar el coste");
   Print(res);
   Print("CSV: Common\\Files\\",fn);
   Alert(res);
  }
//+------------------------------------------------------------------+
