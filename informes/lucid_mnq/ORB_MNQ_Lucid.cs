// ORB_MNQ_Lucid.cs - NinjaTrader 8 (NinjaScript)
// Port del ORB_US100_AGR_v018 (MT5) a futuros MNQ (micro Nasdaq) para Lucid Trading - LucidFlex 50K.
// Proyecto Prop Firm Challenges - Jorge - version 1.00 - 14/11/2026
//
// QUE HACE (misma senal que el v018)
//  - Rango de apertura = 10 primeras velas M1 de la sesion de Nueva York (cierran entre 9:31 y 9:40 ET).
//  - Vela del rango alcista -> LARGO a mercado; bajista -> CORTO; cuerpo < 10 % del rango -> no opera.
//  - Stop = 15 % del ATR(14) diario de ayer (media simple del TR, igual que iATR de MT5).
//  - Reto: trailing al ganar 3R con el stop a 1R del maximo. Fondeada: stop a entrada al ganar 2R.
//  - Salida a las 15:30 ET (14:00 ET en dias de FOMC). Una operacion al dia como maximo.
//  - Filtro de volatilidad del v018: no opera si el ATR% de ayer supera el percentil 90 del ultimo ano.
//  - Festivos y cierres anticipados de la bolsa USA bloqueados (lista del v018).
//
// REGLAS LUCIDFLEX 50K (web oficial support.lucidtrading.com, revisada 14/11/2026)
//  - Perdida maxima (MLL) 2.000 $ con arrastre al cierre del dia: suelo = maximo saldo de cierre - 2.000,
//    que se bloquea en 50.100 $ cuando el saldo de cierre supera 52.100 $. Al pedir un retiro el suelo pasa a 50.100.
//  - Objetivo del reto 3.000 $; consistencia del reto 40 %: el mejor dia <= 40 % del beneficio total.
//  - Tamano maximo reto 4 minis / 40 micros. Fondeada (escalado): 20 micros con beneficio < 1.000 $,
//    30 con < 2.000 $, 40 con 2.000 $ o mas.
//  - Todo cerrado antes de las 16:45 ET. Bots permitidos (prohibidos HFT, microscalping y cobertura entre cuentas).
//  - Perdida diaria (DLL) opcional y "blanda": con 1 operacion al dia no llega a actuar.
//  El EA NO pide retiros: los pide Jorge desde el panel de Lucid (5 dias con >= 150 $, 50 % hasta 2.000 $).
//
// DIMENSIONADO
//  - Riesgo objetivo en $ (RiesgoUSD). Contratos = redondeo de RiesgoUSD / (stop en puntos * valor del punto + coste),
//    sin pasar de RiesgoUSD * (1 + ExcesoMaxPct/100). MNQ: 2 $ por punto; NQ: 20 $ por punto.
//  - Por defecto 350 $ por operacion y SIN recorte cerca del suelo del MLL: en la simulacion de 1 ano (lucid_sim.py)
//    recortar el tamano o dar la cuenta por agotada cerca del suelo baja la media 400-650 EUR (la cuota es barata;
//    es mejor arriesgar el tamano normal y recomprar). Opcional: MultDeslizamiento > 0 (tope por el suelo) y AgotadaPct.
//
// COMO USARLO (ver LEEME_NINJATRADER.md)
//  - Grafico/estrategia sobre MNQ (contrato del mes), velas de 1 minuto, plantilla de horario
//    "CME US Index Futures ETH". En "Days to load" poner 420 (hace falta un ano de velas diarias para el filtro).
//  - Start behavior: Wait until flat.
//  - Al arrancar en una cuenta real: poner SueloMLL (lo que muestra el panel de Lucid) y MejorDiaUSD.
//
// VALIDACION: orb_mnq_ref.py es la replica en Python de este codigo (mismo reloj, mismas reglas).
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Linq;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class ORB_MNQ_Lucid : Strategy
    {
        // ---------------- estado ----------------
        private TimeZoneInfo tzEt;
        private HashSet<DateTime> festivos, fomc;
        private DateTime diaEt = DateTime.MinValue;
        private double rgHi, rgLo, rgOpen, rgClose;
        private int rgBars, rgFirstMin;
        private bool evaluado, operadoHoy, cuentaParada;
        private int dir;                     // 1 largo, -1 corto
        private double riesgoPts, mfe, stopActual;
        private double saldoMaxCierre, suelo, mejorDia, pnlHoy;
        private int diasCobrables;           // dias del ciclo con >= 150 $ (solo informativo)
        private int tradesRegistrados;
        private string ficheroCsv, ficheroEstado;
        private const string SENAL = "ORB";

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "ORB_MNQ_Lucid";
                Description = "ORB US100 v018 portado a MNQ para LucidFlex 50K";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 60;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.Infinite;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 0;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Day;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 20;
                IsInstantiatedOnEachOptimizationIteration = true;

                // 1. Cuenta y fase
                Fase = 0;
                SaldoInicial = 50000;
                PerdidaMaxUSD = 2000;
                SueloBloqueoUSD = 50100;
                SueloMLL = 48000;
                ObjetivoUSD = 3000;
                ConsistenciaPct = 40;
                MejorDiaUSD = 0;
                PararAlSuperar = true;
                // 2. Riesgo
                RiesgoUSD = 350;
                ExcesoMaxPct = 25;
                CosteContratoUSD = 2.0;
                ColchonUSD = 100;
                MultDeslizamiento = 0;      // 0 = sin recorte cerca del suelo (mejor en la simulacion)
                AgotadaPct = 0;             // 0 = off
                PerdidaDiariaUSD = 0;
                MaxMicrosReto = 40;
                MaxMicrosEsc1 = 20;
                MaxMicrosEsc2 = 30;
                MaxMicrosEsc3 = 40;
                // 3. Senal
                MinutosRango = 10;
                MinVelasRango = 8;
                CuerpoMinPct = 10;
                StopAtrPct = 15;
                FiltroVol = true;
                VolPercentil = 90;
                VolDias = 252;
                TrailActR = 3.0;
                TrailDistR = 1.0;
                TrailPasoR = 0.1;
                FondeadaBeR = 2.0;
                // 4. Horario (hora de Nueva York)
                InicioHHMM = 930;
                RetrasoMaxMin = 5;
                SalidaHHMM = 1530;
                SalidaFomcHHMM = 1400;
                DiasExtra = "";
                RegistrarCsv = true;
                ModoValidacion = false;
            }
            else if (State == State.Configure)
            {
                AddDataSeries(BarsPeriodType.Day, 1);   // velas diarias de la misma plantilla de horario (ETH: 18:00-17:00 ET)
            }
            else if (State == State.DataLoaded)
            {
                tzEt = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
                festivos = ParseFechas(FESTIVOS + "," + (DiasExtra ?? ""));
                fomc = ParseFechas(FOMC);
                string dir0 = Path.Combine(NinjaTrader.Core.Globals.UserDataDir, "ORB_MNQ");
                Directory.CreateDirectory(dir0);
                string cuenta = Account != null ? Account.Name : "SinCuenta";
                ficheroCsv = Path.Combine(dir0, "ORB_MNQ_" + Limpia(cuenta) + "_ops.csv");
                ficheroEstado = Path.Combine(dir0, "ORB_MNQ_" + Limpia(cuenta) + "_estado.txt");
                suelo = SueloMLL;
                mejorDia = MejorDiaUSD;
                saldoMaxCierre = SaldoInicial;
                tradesRegistrados = 0;
            }
            else if (State == State.Realtime)
            {
                // en real: se olvida lo simulado con el historico; el saldo sale de la cuenta y el suelo y el mejor dia,
                // de los parametros o del fichero de estado (el que sea mayor)
                cuentaParada = false; suelo = SueloMLL; mejorDia = MejorDiaUSD; saldoMaxCierre = SaldoInicial; diasCobrables = 0;
                CargarEstado();
                double s = Saldo();
                saldoMaxCierre = Math.Max(saldoMaxCierre, s);
                tradesRegistrados = SystemPerformance.AllTrades.Count;
                Print(string.Format(CultureInfo.InvariantCulture,
                    "ORB_MNQ_Lucid v1.00 | cuenta {0} | {1} | saldo {2:F2} | suelo MLL {3:F2} | mejor dia {4:F2} | riesgo {5:F0} $",
                    Account != null ? Account.Name : "-", Fase != 2 ? "RETO" : "FONDEADA", s, suelo, mejorDia, RiesgoUSD));
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0) return;
            if (CurrentBars[0] < BarsRequiredToTrade || CurrentBars[1] < 15) return;

            DateTime et = TimeZoneInfo.ConvertTime(Time[0], NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo, tzEt);
            int min = et.Hour * 60 + et.Minute;
            int ini = (InicioHHMM / 100) * 60 + InicioHHMM % 100;
            int finRango = ini + MinutosRango;

            if (et.Date != diaEt) NuevoDia(et.Date);

            // ---- gestion de la posicion abierta (al cierre de cada vela, como la replica) ----
            if (Position.MarketPosition != MarketPosition.Flat)
            {
                GestionarPosicion(et, min);
                return;
            }

            // ---- construir el rango: velas que cierran en (9:30, 9:40] ----
            if (min > ini && min <= finRango)
            {
                if (rgBars == 0) { rgOpen = Open[0]; rgHi = High[0]; rgLo = Low[0]; rgFirstMin = min; }
                rgHi = Math.Max(rgHi, High[0]); rgLo = Math.Min(rgLo, Low[0]); rgClose = Close[0]; rgBars++;
            }
            if (!evaluado && min >= finRango && min <= finRango + RetrasoMaxMin)
            {
                evaluado = true;
                if (min == finRango) Evaluar(et);
                else Print(et + " ORB: no hay vela de cierre del rango a su hora: no opera hoy.");
            }
        }

        // ------------------------------------------------------------------
        private void Evaluar(DateTime et)
        {
            if (cuentaParada) { Print(et + " ORB: cuenta parada (reto superado o agotada)."); return; }
            if (festivos.Contains(et.Date)) { Print(et + " ORB: hoy no opera: festivo o cierre anticipado."); return; }
            if (operadoHoy) return;
            int ini = (InicioHHMM / 100) * 60 + InicioHHMM % 100;
            if (rgBars < MinVelasRango || rgFirstMin > ini + 3) { Print(et + " ORB: hoy no opera: faltan datos de la apertura."); return; }
            double rango = rgHi - rgLo;
            if (rango <= 0) return;
            double cuerpo = rgClose - rgOpen;
            if (Math.Abs(cuerpo) < rango * CuerpoMinPct / 100.0)
            { Print(string.Format(CultureInfo.InvariantCulture, "{0} ORB: hoy no opera: vela del rango sin cuerpo ({1:F2} de {2:F2}).", et, Math.Abs(cuerpo), rango)); return; }

            double atr = AtrDiario(0);
            if (atr <= 0) { Print(et + " ORB: sin ATR diario (faltan velas diarias: Days to load >= 420)."); return; }
            if (FiltroVol)
            {
                double pct;
                if (VolDemasiadoAlta(out pct))
                { Print(string.Format(CultureInfo.InvariantCulture, "{0} ORB: hoy no opera: volatilidad extrema (ATR% en el percentil {1:F0}, limite {2:F0}).", et, pct, VolPercentil)); return; }
            }

            double tick = TickSize;
            riesgoPts = Math.Max(tick, Math.Round(atr * StopAtrPct / 100.0 / tick) * tick);
            int qty = Contratos(riesgoPts, et);
            if (qty < 1) return;

            dir = cuerpo > 0 ? 1 : -1;
            mfe = 0;
            int ticks = (int)Math.Round(riesgoPts / tick);
            SetStopLoss(SENAL, CalculationMode.Ticks, ticks, false);
            if (dir == 1) EnterLong(qty, SENAL); else EnterShort(qty, SENAL);
            operadoHoy = true;
            stopActual = double.NaN;   // se fija con el precio de entrada real
            Print(string.Format(CultureInfo.InvariantCulture, "{0} ORB: {1} {2} contratos | stop {3:F2} pts ({4} ticks) | riesgo {5:F0} $ | ATR {6:F1}",
                et, dir == 1 ? "LARGO" : "CORTO", qty, riesgoPts, ticks, qty * (riesgoPts * Instrument.MasterInstrument.PointValue + CosteContratoUSD), atr));
        }

        private void GestionarPosicion(DateTime et, int min)
        {
            double ent = Position.AveragePrice;
            if (double.IsNaN(stopActual)) stopActual = ent - dir * riesgoPts;
            double fav = dir == 1 ? High[0] - ent : ent - Low[0];
            mfe = Math.Max(mfe, fav);

            bool fomcHoy = fomc.Contains(et.Date);
            int hhmm = fomcHoy ? SalidaFomcHHMM : SalidaHHMM;
            int fin = (hhmm / 100) * 60 + hhmm % 100;
            if (min >= fin) { Salir("hora de salida" + (fomcHoy ? " (FOMC)" : "")); return; }

            double nuevo = double.NaN;
            if (Fase != 2 && TrailActR > 0 && mfe >= TrailActR * riesgoPts)
            {
                double ns = ent + dir * (mfe - TrailDistR * riesgoPts);
                if (dir * (ns - stopActual) >= TrailPasoR * riesgoPts) nuevo = ns;
            }
            if (Fase == 2 && FondeadaBeR > 0 && mfe >= FondeadaBeR * riesgoPts && dir * (ent - stopActual) > 0)
                nuevo = ent;
            if (!double.IsNaN(nuevo))
            {
                nuevo = Instrument.MasterInstrument.RoundToTickSize(nuevo);
                // si el precio ya esta al otro lado del stop nuevo, la orden seria rechazada: se sale a mercado
                // (en la replica el stop se llena en la apertura de la vela siguiente: mismo resultado)
                bool valido = dir == 1 ? Close[0] > nuevo + TickSize : Close[0] < nuevo - TickSize;
                if (!valido) { Salir("stop nuevo ya superado"); return; }
                SetStopLoss(SENAL, CalculationMode.Price, nuevo, false);
                stopActual = nuevo;
            }
        }

        private void Salir(string motivo)
        {
            if (Position.MarketPosition == MarketPosition.Long) ExitLong("ORB_X", SENAL);
            else if (Position.MarketPosition == MarketPosition.Short) ExitShort("ORB_X", SENAL);
            Print(Time[0] + " ORB: salida a mercado: " + motivo);
        }

        // ------------------------------------------------------------------
        private int Contratos(double stopPts, DateTime et)
        {
            double pv = Instrument.MasterInstrument.PointValue;      // MNQ 2 $, NQ 20 $
            double porContrato = stopPts * pv + CosteContratoUSD;
            if (porContrato <= 0) return 0;
            if (ModoValidacion) return 1;                              // backtest de validacion: 1 contrato, sin reglas de cuenta
            int q = (int)Math.Round(RiesgoUSD / porContrato);
            if (q * porContrato > RiesgoUSD * (1 + ExcesoMaxPct / 100.0)) q--;

            double s = Saldo();
            double margen = s - suelo - ColchonUSD;
            if (AgotadaPct > 0 && margen < AgotadaPct / 100.0 * RiesgoUSD)
            {
                cuentaParada = true;
                Print(string.Format(CultureInfo.InvariantCulture, "{0} ORB: CUENTA AGOTADA: margen hasta el suelo {1:F2} $ < {2:F0} % del riesgo. Comprar otra evaluacion.", et, s - suelo, AgotadaPct));
                return 0;
            }
            if (MultDeslizamiento > 0)
            {
                int qMll = (int)Math.Floor(margen / (porContrato * MultDeslizamiento));
                q = Math.Min(q, qMll);
            }
            if (PerdidaDiariaUSD > 0)
            {
                int qDll = (int)Math.Floor((PerdidaDiariaUSD + Math.Min(0, pnlHoy) - ColchonUSD) / (porContrato * Math.Max(1.0, MultDeslizamiento)));
                q = Math.Min(q, qDll);
            }
            // tope de tamano de Lucid (en micros; un mini = 10 micros)
            bool esMicro = pv < 10;
            int topeMicros = Fase != 2 ? MaxMicrosReto
                           : (s - SaldoInicial < 1000 ? MaxMicrosEsc1 : (s - SaldoInicial < 2000 ? MaxMicrosEsc2 : MaxMicrosEsc3));
            int tope = esMicro ? topeMicros : topeMicros / 10;
            q = Math.Min(q, tope);
            if (q < 1) Print(string.Format(CultureInfo.InvariantCulture, "{0} ORB: hoy no opera: 0 contratos (stop {1:F2} pts = {2:F0} $ por contrato, margen {3:F0} $).", et, stopPts, porContrato, margen));
            return Math.Max(0, q);
        }

        private double Saldo()
        {
            if (State == State.Realtime && Account != null)
            {
                double v = Account.Get(AccountItem.CashValue, Currency.UsDollar);
                if (v > 0) return v;
            }
            return SaldoInicial + SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
        }

        // ATR(14) diario como iATR de MT5: media simple del rango verdadero. k = 0 -> ultima vela diaria cerrada (ayer).
        private double AtrDiario(int k)
        {
            if (CurrentBars[1] < k + 14) return 0;
            double sum = 0;
            for (int j = k; j < k + 14; j++)
            {
                double h = Highs[1][j], l = Lows[1][j], pc = Closes[1][j + 1];
                sum += Math.Max(h - l, Math.Max(Math.Abs(h - pc), Math.Abs(l - pc)));
            }
            return sum / 14.0;
        }

        private bool VolDemasiadoAlta(out double pct)
        {
            pct = 0;
            double c0 = Closes[1][0];
            double a0 = AtrDiario(0);
            if (c0 <= 0 || a0 <= 0) return false;
            double cur = a0 / c0;
            int below = 0, cnt = 0;
            for (int i = 1; i <= VolDias; i++)
            {
                if (CurrentBars[1] < i + 14) break;
                double ci = Closes[1][i];
                double ai = AtrDiario(i);
                if (ci <= 0 || ai <= 0) continue;
                cnt++;
                if (ai / ci < cur) below++;
            }
            if (cnt < 120) return false;              // poca historia: no filtra (como el v018)
            pct = 100.0 * below / cnt;
            return pct > VolPercentil;
        }

        // ------------------------------------------------------------------
        private void NuevoDia(DateTime d)
        {
            // cierre del dia anterior: mejor dia, dias cobrables, suelo del MLL (arrastre al cierre del dia)
            if (diaEt != DateTime.MinValue)
            {
                if (pnlHoy > mejorDia) mejorDia = pnlHoy;
                if (pnlHoy >= 150) diasCobrables++;
                double s = Saldo();
                saldoMaxCierre = Math.Max(saldoMaxCierre, s);
                double nuevoSuelo = Math.Min(saldoMaxCierre - PerdidaMaxUSD, SueloBloqueoUSD);
                if (nuevoSuelo > suelo) suelo = nuevoSuelo;
                if (Fase != 2 && PararAlSuperar && !ModoValidacion)
                {
                    double ben = s - SaldoInicial;
                    if (ben >= ObjetivoUSD && mejorDia <= ConsistenciaPct / 100.0 * ben && !cuentaParada)
                    {
                        cuentaParada = true;
                        Print(string.Format(CultureInfo.InvariantCulture, "{0:d} ORB: RETO SUPERADO: beneficio {1:F2} $, mejor dia {2:F2} $ ({3:F0} %). El EA deja de operar.", diaEt, ben, mejorDia, 100 * mejorDia / ben));
                    }
                    else if (ben >= ObjetivoUSD)
                        Print(string.Format(CultureInfo.InvariantCulture, "{0:d} ORB: objetivo alcanzado pero el mejor dia ({1:F2} $) pasa del {2:F0} % del beneficio: sigue operando.", diaEt, mejorDia, ConsistenciaPct));
                }
                if (State == State.Realtime) GuardarEstado();
            }
            diaEt = d; pnlHoy = 0; rgBars = 0; evaluado = false; operadoHoy = false;
        }

        protected override void OnPositionUpdate(Position position, double averagePrice, int quantity, MarketPosition marketPosition)
        {
            if (marketPosition != MarketPosition.Flat) return;
            var all = SystemPerformance.AllTrades;
            for (int i = tradesRegistrados; i < all.Count; i++)
            {
                Trade t = all[i];
                double neto = t.ProfitCurrency;      // ya descuenta la comision de la plantilla
                pnlHoy += neto;
                double rDin = t.Quantity * (riesgoPts * Instrument.MasterInstrument.PointValue + CosteContratoUSD);
                if (RegistrarCsv && (State == State.Realtime || ModoValidacion)) Csv(t, neto, rDin);
            }
            tradesRegistrados = all.Count;
        }

        private void Csv(Trade t, double neto, double rDin)
        {
            try
            {
                bool nuevo = !File.Exists(ficheroCsv);
                using (var w = new StreamWriter(ficheroCsv, true))
                {
                    if (nuevo) w.WriteLine("Fecha;Hora;Instrumento;Lado;Contratos;PrecioEntrada;PrecioSalida;Salida;StopPts;RiesgoUSD;PnL_neto;Comision;R;Saldo;SueloMLL;Fase");
                    w.WriteLine(string.Join(";", new string[] {
                        t.Exit.Time.ToString("yyyy.MM.dd"), t.Exit.Time.ToString("HH:mm"), Instrument.FullName,
                        t.Entry.MarketPosition == MarketPosition.Long ? "LONG" : "SHORT", t.Quantity.ToString(),
                        t.Entry.Price.ToString(CultureInfo.InvariantCulture), t.Exit.Price.ToString(CultureInfo.InvariantCulture), t.Exit.Name,
                        riesgoPts.ToString("F2", CultureInfo.InvariantCulture), rDin.ToString("F2", CultureInfo.InvariantCulture),
                        neto.ToString("F2", CultureInfo.InvariantCulture), t.Commission.ToString("F2", CultureInfo.InvariantCulture),
                        (rDin > 0 ? neto / rDin : 0).ToString("F3", CultureInfo.InvariantCulture),
                        Saldo().ToString("F2", CultureInfo.InvariantCulture), suelo.ToString("F2", CultureInfo.InvariantCulture), Fase != 2 ? "reto" : "fondeada" }));
                }
            }
            catch (Exception e) { Print("ORB: no se pudo escribir el CSV: " + e.Message); }
        }

        private void GuardarEstado()
        {
            try
            {
                File.WriteAllText(ficheroEstado, string.Format(CultureInfo.InvariantCulture,
                    "suelo={0:F2}\nmejorDia={1:F2}\nsaldoMaxCierre={2:F2}\ndiasCobrables={3}\nfecha={4:yyyy-MM-dd}\n", suelo, mejorDia, saldoMaxCierre, diasCobrables, diaEt));
            }
            catch (Exception e) { Print("ORB: no se pudo guardar el estado: " + e.Message); }
        }

        private void CargarEstado()
        {
            try
            {
                if (!File.Exists(ficheroEstado)) return;
                foreach (string ln in File.ReadAllLines(ficheroEstado))
                {
                    string[] kv = ln.Split('=');
                    if (kv.Length != 2) continue;
                    double v;
                    if (!double.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out v)) continue;
                    if (kv[0] == "suelo") suelo = Math.Max(suelo, v);                // nunca baja (salvo cuenta nueva: borrar el fichero)
                    else if (kv[0] == "mejorDia") mejorDia = Math.Max(mejorDia, v);
                    else if (kv[0] == "saldoMaxCierre") saldoMaxCierre = Math.Max(saldoMaxCierre, v);
                    else if (kv[0] == "diasCobrables") diasCobrables = (int)v;
                }
            }
            catch (Exception e) { Print("ORB: no se pudo leer el estado: " + e.Message); }
        }

        private static HashSet<DateTime> ParseFechas(string s)
        {
            var h = new HashSet<DateTime>();
            foreach (string p in s.Split(new[] { ',', ';', ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries))
            {
                DateTime d;
                if (DateTime.TryParseExact(p.Trim(), "yyyy.MM.dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) h.Add(d.Date);
            }
            return h;
        }

        private static string Limpia(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s;
        }

        // Festivos y cierres anticipados de la bolsa USA (lista del v018) y fechas del FOMC
        private const string FESTIVOS =
            "2024.01.01,2024.01.15,2024.02.19,2024.03.29,2024.05.27,2024.06.19,2024.07.03,2024.07.04,2024.09.02,2024.11.28,2024.11.29,2024.12.24,2024.12.25," +
            "2025.01.01,2025.01.09,2025.01.20,2025.02.17,2025.04.18,2025.05.26,2025.06.19,2025.07.03,2025.07.04,2025.09.01,2025.11.27,2025.11.28,2025.12.24,2025.12.25," +
            "2026.01.01,2026.01.19,2026.02.16,2026.04.03,2026.05.25,2026.06.19,2026.07.03,2026.09.07,2026.11.26,2026.11.27,2026.12.24,2026.12.25," +
            "2027.01.01,2027.01.18,2027.02.15,2027.03.26,2027.05.31,2027.06.18,2027.07.05,2027.09.06,2027.11.25,2027.11.26,2027.12.24";
        private const string FOMC =
            "2024.01.31,2024.03.20,2024.05.01,2024.06.12,2024.07.31,2024.09.18,2024.11.07,2024.12.18," +
            "2025.01.29,2025.03.19,2025.05.07,2025.06.18,2025.07.30,2025.09.17,2025.10.29,2025.12.10," +
            "2026.01.28,2026.03.18,2026.04.29,2026.06.17,2026.07.29,2026.09.16,2026.10.28,2026.12.09," +
            "2027.01.27,2027.03.17,2027.04.28,2027.06.09,2027.07.28,2027.09.15,2027.10.27,2027.12.08";

        #region Parametros
        [NinjaScriptProperty, Range(0, 2), Display(Name = "Fase (0 = reto, 2 = fondeada; 1 = como el reto)", Order = 1, GroupName = "1. Cuenta Lucid")]
        public int Fase { get; set; }
        [NinjaScriptProperty, Display(Name = "Saldo inicial", Order = 2, GroupName = "1. Cuenta Lucid")]
        public double SaldoInicial { get; set; }
        [NinjaScriptProperty, Display(Name = "Perdida maxima (MLL) $", Order = 3, GroupName = "1. Cuenta Lucid")]
        public double PerdidaMaxUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Suelo bloqueado $", Order = 4, GroupName = "1. Cuenta Lucid")]
        public double SueloBloqueoUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Suelo MLL actual $ (panel de Lucid)", Order = 5, GroupName = "1. Cuenta Lucid")]
        public double SueloMLL { get; set; }
        [NinjaScriptProperty, Display(Name = "Objetivo del reto $", Order = 6, GroupName = "1. Cuenta Lucid")]
        public double ObjetivoUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Consistencia del reto %", Order = 7, GroupName = "1. Cuenta Lucid")]
        public double ConsistenciaPct { get; set; }
        [NinjaScriptProperty, Display(Name = "Mejor dia hasta ahora $", Order = 8, GroupName = "1. Cuenta Lucid")]
        public double MejorDiaUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Parar al superar el reto", Order = 9, GroupName = "1. Cuenta Lucid")]
        public bool PararAlSuperar { get; set; }

        [NinjaScriptProperty, Display(Name = "Riesgo por operacion $", Order = 1, GroupName = "2. Riesgo")]
        public double RiesgoUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Exceso maximo al redondear %", Order = 2, GroupName = "2. Riesgo")]
        public double ExcesoMaxPct { get; set; }
        [NinjaScriptProperty, Display(Name = "Coste ida y vuelta por contrato $", Order = 3, GroupName = "2. Riesgo")]
        public double CosteContratoUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Colchon sobre el suelo $", Order = 4, GroupName = "2. Riesgo")]
        public double ColchonUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Tope por el suelo: perdida x deslizamiento (0 = off)", Order = 5, GroupName = "2. Riesgo")]
        public double MultDeslizamiento { get; set; }
        [NinjaScriptProperty, Display(Name = "Cuenta agotada si margen < X % del riesgo (0 = off)", Order = 6, GroupName = "2. Riesgo")]
        public double AgotadaPct { get; set; }
        [NinjaScriptProperty, Display(Name = "Perdida diaria de Lucid $ (0 = sin DLL)", Order = 7, GroupName = "2. Riesgo")]
        public double PerdidaDiariaUSD { get; set; }
        [NinjaScriptProperty, Display(Name = "Max micros en el reto", Order = 8, GroupName = "2. Riesgo")]
        public int MaxMicrosReto { get; set; }
        [NinjaScriptProperty, Display(Name = "Max micros fondeada (< 1.000 $)", Order = 9, GroupName = "2. Riesgo")]
        public int MaxMicrosEsc1 { get; set; }
        [NinjaScriptProperty, Display(Name = "Max micros fondeada (< 2.000 $)", Order = 10, GroupName = "2. Riesgo")]
        public int MaxMicrosEsc2 { get; set; }
        [NinjaScriptProperty, Display(Name = "Max micros fondeada (>= 2.000 $)", Order = 11, GroupName = "2. Riesgo")]
        public int MaxMicrosEsc3 { get; set; }

        [NinjaScriptProperty, Display(Name = "Minutos del rango", Order = 1, GroupName = "3. Senal")]
        public int MinutosRango { get; set; }
        [NinjaScriptProperty, Display(Name = "Velas minimas en el rango", Order = 2, GroupName = "3. Senal")]
        public int MinVelasRango { get; set; }
        [NinjaScriptProperty, Display(Name = "Cuerpo minimo % del rango", Order = 3, GroupName = "3. Senal")]
        public double CuerpoMinPct { get; set; }
        [NinjaScriptProperty, Display(Name = "Stop % del ATR diario", Order = 4, GroupName = "3. Senal")]
        public double StopAtrPct { get; set; }
        [NinjaScriptProperty, Display(Name = "Filtro de volatilidad", Order = 5, GroupName = "3. Senal")]
        public bool FiltroVol { get; set; }
        [NinjaScriptProperty, Display(Name = "Percentil maximo de ATR%", Order = 6, GroupName = "3. Senal")]
        public double VolPercentil { get; set; }
        [NinjaScriptProperty, Display(Name = "Dias del percentil", Order = 7, GroupName = "3. Senal")]
        public int VolDias { get; set; }
        [NinjaScriptProperty, Display(Name = "Reto: trailing desde X R", Order = 8, GroupName = "3. Senal")]
        public double TrailActR { get; set; }
        [NinjaScriptProperty, Display(Name = "Reto: distancia del trailing R", Order = 9, GroupName = "3. Senal")]
        public double TrailDistR { get; set; }
        [NinjaScriptProperty, Display(Name = "Reto: paso minimo del trailing R", Order = 10, GroupName = "3. Senal")]
        public double TrailPasoR { get; set; }
        [NinjaScriptProperty, Display(Name = "Fondeada: stop a entrada a X R", Order = 11, GroupName = "3. Senal")]
        public double FondeadaBeR { get; set; }

        [NinjaScriptProperty, Display(Name = "Apertura (HHMM Nueva York)", Order = 1, GroupName = "4. Horario")]
        public int InicioHHMM { get; set; }
        [NinjaScriptProperty, Display(Name = "Retraso maximo de entrada (min)", Order = 2, GroupName = "4. Horario")]
        public int RetrasoMaxMin { get; set; }
        [NinjaScriptProperty, Display(Name = "Salida (HHMM Nueva York)", Order = 3, GroupName = "4. Horario")]
        public int SalidaHHMM { get; set; }
        [NinjaScriptProperty, Display(Name = "Salida dias FOMC (HHMM NY)", Order = 4, GroupName = "4. Horario")]
        public int SalidaFomcHHMM { get; set; }
        [NinjaScriptProperty, Display(Name = "Dias extra sin operar (AAAA.MM.DD,...)", Order = 5, GroupName = "4. Horario")]
        public string DiasExtra { get; set; }
        [NinjaScriptProperty, Display(Name = "Registrar operaciones en CSV", Order = 6, GroupName = "4. Horario")]
        public bool RegistrarCsv { get; set; }
        [NinjaScriptProperty, Display(Name = "Modo validacion (1 contrato, sin reglas de cuenta)", Order = 7, GroupName = "4. Horario")]
        public bool ModoValidacion { get; set; }
        #endregion
    }
}
