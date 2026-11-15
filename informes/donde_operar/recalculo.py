"""Recalculo de las ventajas reales con los costes de cada sitio (14-11-2026). Mismas reglas, series ya guardadas.
Series: gotobi_USDJPY_ops.csv (yes-lab rama claude/project-thread-gpiyvs, metodo/revision/), metodo/v3/orb_asia (JP225),
metodo/v3/orb_cripto_medio (BTC/ETH), orb_acciones/indices_2012 (US100/US500/US30, víspera)."""
import glob, sys, numpy as np, pandas as pd, pandas_market_calendars as mcal
YL = "/home/user/yes-lab/"; SC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/sc/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))
filas = []
def fila(est, sitio, coste_txt, n, ops_anio, nota=""):
    m = n.index >= "2024-01-01" if isinstance(n.index, pd.DatetimeIndex) else None
    filas.append(dict(estrategia=est, sitio=sitio, coste=coste_txt, neto_R=round(n.mean(), 3), t=round(t(n), 2),
                      neto_2024_26=round(n[m].mean(), 3) if m is not None else np.nan, R_anio=round(n.mean() * ops_anio, 1), nota=nota))

# ---------------- gotobi USDJPY 08:00->09:55 JST (stop 0,25 rango14)
g = pd.read_csv(SC + "gotobi.csv", parse_dates=["fecha"]).set_index("fecha"); g = g[g.gotobi]
opa = len(g) / ((g.index.max() - g.index.min()).days / 365.25)
COM = lambda usd_rt, px=150: usd_rt * px / 1000        # pips de comision por $ ida y vuelta por lote 100k USD
sitios_g = [("FTMO (medido)", 1.52, "horquilla 0,75 media + comisión 0,79"),
            ("IBKR spot (0,2 pb/lado)", COM(4) + 0.3, "comisión 0,60 + horquilla ~0,3 (supuesta)"),
            ("IBKR spot, horquilla 0,5", COM(4) + 0.5, "comisión 0,60 + horquilla 0,5"),
            ("Darwinex (0,005 % i/v)", 0.75 + 0.5, "comisión 0,75 + horquilla ~0,5 (supuesta)"),
            ("Tickmill / IC cTrader (6 $)", COM(6) + 0.4, "comisión 0,90 + horquilla ~0,4"),
            ("IC MT5 / Pepperstone (7 $)", COM(7) + 0.4, "comisión 1,05 + horquilla ~0,4"),
            ("CME 6J (1 tick + 5 $)", 1.12 + 0.9, "tick 6,25 $ = 1,1 pips + comisión ~0,9"),
            ("Umbral del disparador", 0.8, "")]
for s, c, txt in sitios_g:
    n = g.r_bruto - c / g.dist_pips
    fila("Gotobi USDJPY", s, f"{c:.2f} pips ({txt})", n, opa, f"costes x2: {(g.r_bruto - 2*c/g.dist_pips).mean():+.3f} R")

# ---------------- ORB JP225 apertura Tokio (stop 0,15 ATR)
jp = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(YL + "metodo/v3/orb_asia/asia_JP225_*.csv"))); jp["fecha"] = pd.to_datetime(jp.fecha)
jp = jp.set_index("fecha").sort_index().dropna(subset=["r"]); jp = jp[jp.index.dayofweek < 5]
opa = len(jp) / ((jp.index.max() - jp.index.min()).days / 365.25)
PX = 60000.0   # nivel actual: el tick es fijo en puntos, así que el coste de hoy en % se aplica a toda la historia
for s, pct, txt in [("FTMO CFD (medido)", 0.000157, "0,0157 % = 9,4 pts"),
                    ("CFD ECN (IC/Pepperstone, ~8-10 pts)", 9 / PX, "9 pts supuestos"),
                    ("CME NKD vía IBKR (1 tick + 4,7 $)", (5 + 4.7 / 5) / PX, "5,9 pts = 0,0099 %"),
                    ("OSE mini vía IBKR (1 tick + ~¥160)", (5 + 1.6) / PX, "6,6 pts = 0,011 %"),
                    ("Topstep NKD (1 tick + 5,32 $)", (5 + 5.32 / 5) / PX, "6,1 pts = 0,010 %"),
                    ("NKD con 2 ticks (horquilla abierta)", (10 + 1) / PX, "11 pts = 0,018 %")]:
    fila("ORB JP225", s, txt, jp.r - pct * jp.px / jp.dist, opa)

# ---------------- ORB cripto 9:30 NY (rango 10 min, stop 0,15 ATR)
for nom in ("BTC", "ETH"):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(YL + f"metodo/v3/orb_cripto_medio/medio_{nom}USD_*.csv"))); d["fecha"] = pd.to_datetime(d.fecha)
    d = d.set_index("fecha").sort_index().dropna(subset=["r10"]); d = d[(d.index.dayofweek < 5) & (d.index >= "2021-03-01")]
    opa = len(d) / ((d.index.max() - d.index.min()).days / 365.25); k = d.px / (0.15 * d.atr)
    for s, pct, txt in [("FTMO CFD (medido)", 0.00065 + (0.000012 if nom == "BTC" else 0.00025), "0,065 % + horquilla"),
                        ("Darwinex CFD (0,05 %/orden)", 0.0010 + 0.0002, "0,10 % + horquilla"),
                        ("Pepperstone CFD sin comisión (horquilla ~0,04 %)", 0.0004, "supuesta"),
                        ("Perpetuos Hyperliquid/Binance (taker 0,045 %/lado)", 0.0009 + 0.00002, "0,09 % i/v"),
                        ("Umbral del disparador", 0.0002, "0,02 % i/v")]:
        fila(f"ORB {nom} 9:30 NY", s, txt, d.r10 - pct * k, opa)

# ---------------- víspera de festivo, apertura -> cierre (regla A), índices US 2012-26 precio medio
nyse = mcal.get_calendar("NYSE"); dias = nyse.valid_days("2011-01-01", "2027-01-31").tz_localize(None)
bd = pd.bdate_range("2011-01-01", "2027-01-31"); sig = pd.Series(dias[1:], index=dias[:-1])
vis = {dd for dd, nx in sig.items() if len(bd[(bd > dd) & (bd < nx)]) > 0}
todos = []
for sim, c_cfd, c_fut in (("US100", 0.000049, 0.00002), ("US500", 0.00005, 0.00005), ("US30", 0.00006, 0.00004)):
    x = pd.concat([pd.read_csv(YL + f"orb_acciones/{c}/{sim}.csv", parse_dates=["fecha"]) for c in ("indices_2012", "indices")]).set_index("fecha")
    tr = pd.concat([x.h - x.l, (x.h - x.c.shift()).abs(), (x.l - x.c.shift()).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(20).mean().shift(1); x = x.dropna(subset=["atr", "o930", "c"])
    x["r"] = (x.c - x.o930) / x.atr; x["pb"] = (x.c / x.o930 - 1) * 1e4; x["k"] = x.o930 / x.atr
    x["vis"] = x.index.isin(vis); x["sim"] = sim; x["c_cfd"] = c_cfd; x["c_fut"] = c_fut; todos.append(x)
v = pd.concat(todos); e = v[v.vis]
opa_c = e.index.nunique() / 15.1
for s, col in (("FTMO CFD (horquilla medida)", "c_cfd"), ("Futuros ES/NQ/YM (1 tick + comisión)", "c_fut")):
    n = (e.r - e[col] * e.k).groupby(level=0).mean()      # media de los 3 índices por fecha (están correlados)
    fila("Víspera festivo US (3 índices, por fecha)", s, col, n, opa_c,
         f"bruto {e.r.mean():+.3f} R = {e.pb.mean():+.1f} pb; día normal {v[~v.vis].r.mean():+.3f} R")
r = pd.DataFrame(filas); r.to_csv("/mnt/project-files/donde-operar/recalculo.csv", index=False, sep=";")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); print(r.to_string(index=False))
print("víspera: fechas", e.index.nunique(), "| por año", round(opa_c, 1), "| pb bruto por índice", e.groupby("sim").pb.mean().round(1).to_dict())
