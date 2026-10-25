# Información no de precio en forex y oro (2026-10-25). Criterios fijados antes:
# ajuste 2006-2016, OOS 2017-2026, coste al doble; pasa con t OOS >= 2,5 y mismo signo en ajuste.
# Retornos en unidades de volatilidad del periodo (r / desv. típica de los 36 periodos previos).
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/mnt/project-files/ea-pons-nnfx"); import torneo_vp as T
M = "/home/claude/yes-lab/datos_macro/"
PX = {}
for s in T.SYMS:
    x = pd.read_csv(f"/tmp/claude-0/mt5/{s}_D1.csv"); x["Date"] = pd.to_datetime(x.Date.str.replace(".", "-"))
    PX[s] = x.set_index("Date")[["Open", "Close"]].sort_index()
CC = {"USD": "US", "EUR": "EZ", "GBP": "GB", "JPY": "JP", "AUD": "AU", "CAD": "CA", "NZD": "NZ", "CHF": "CH"}
LT = {"USD": None, "EUR": "DE", "GBP": "GB", "JPY": "JP", "AUD": "AU", "CAD": "CA", "NZD": "NZ", "CHF": "CH"}
def fred(sid):
    x = pd.read_csv(M + f"fred/{sid}.csv"); x.columns = ["d", "v"]; x["d"] = pd.to_datetime(x.d)
    return pd.to_numeric(x.v, errors="coerce").set_axis(x.d).dropna()
R3 = {k: fred(f"IR3TIB01{v}M156N") for k, v in CC.items()}
ust10 = None
RL = {k: fred(f"IRLTLT01{v}M156N") for k, v in LT.items() if v}
# 10 años EE. UU.: DGS2 es 2 años diario; usamos media mensual del 2 años como proxy de tipo largo de EE. UU.
RL["USD"] = fred("DGS2").resample("MS").mean()
SWAP_MARKUP = 0.015                                   # coste anual supuesto de swap del bróker, contra en ambos lados

def monthly(s):
    d = PX[s]; m = d.resample("MS").agg({"Open": "first", "Close": "last"}).dropna()
    return m, np.log(m.Close / m.Open), T.COST[s] / m.Open

def lagged(ser, idx, lag=2):                        # dato del mes t-lag (publicación con retraso)
    return ser.reindex(ser.index.union(idx)).ffill().shift(0).reindex(idx).shift(lag)

def evaluate(name, rows):
    df = pd.DataFrame(rows, columns=["dt", "R", "R2"])
    out = []
    for a, b in (("2006", "2016"), ("2017", "2026")):
        q = df[(df.dt >= a) & (df.dt <= b + "-12-31")]
        if len(q) < 20: out.append("n<20"); continue
        t = q.R2.mean() / q.R2.std() * np.sqrt(len(q)); yp = (q.groupby(q.dt.dt.year).R2.mean() > 0).mean()
        out.append(f"n {len(q)} media {q.R2.mean():+.3f} t {t:+.2f} años+ {yp:.0%}")
    print(f"{name:42s} | ajuste: {out[0]} | OOS: {out[1]}")

FX = [s for s in T.SYMS if s != "XAUUSD"]
def carry_tests():
    for kind in ("nivel", "cambio3m", "largo_cambio3m"):
        for swap in (True, False):
            rows = []
            for s in FX:
                b, q = s[:3], s[3:]; m, r, cost = monthly(s)
                src = R3 if kind != "largo_cambio3m" else RL
                diff = lagged(src[b], m.index) - lagged(src[q], m.index)
                sig = np.sign(diff) * (diff.abs() > 0.5) if kind == "nivel" else np.sign(diff - diff.shift(3))
                vol = r.rolling(36).std().shift(1)
                carry = diff / 100 / 12
                for dt in m.index:
                    sg = sig.get(dt, np.nan)
                    if not np.isfinite(sg) or sg == 0 or not np.isfinite(vol[dt]): continue
                    extra = (sg * carry[dt] - SWAP_MARKUP / 12) if swap else 0.0
                    g = sg * r[dt] + extra
                    rows.append((dt, (g - cost[dt]) / vol[dt], (g - 2 * cost[dt]) / vol[dt]))
            evaluate(f"carry {kind} {'con swap' if swap else 'solo precio'}", rows)

COTC = {"EURUSD": ("099741", 1), "GBPUSD": ("096742", 1), "USDJPY": ("097741", -1), "AUDUSD": ("232741", 1),
        "USDCAD": ("090741", -1), "NZDUSD": ("112741", 1), "USDCHF": ("092741", -1), "XAUUSD": ("088691", 1)}
def cot_tests():
    c = pd.read_csv(M + "cot/cot_divisas_oro.csv", low_memory=False)
    c["code"] = c["CFTC Contract Market Code"].astype(str).str.strip().str.zfill(6)
    c["d"] = pd.to_datetime(c["As of Date in Form YYYY-MM-DD"])
    for col in ("Open Interest (All)", "Noncommercial Positions-Long (All)", "Noncommercial Positions-Short (All)"):
        c[col] = pd.to_numeric(c[col].astype(str).str.replace(",", ""), errors="coerce")
    c["net"] = (c["Noncommercial Positions-Long (All)"] - c["Noncommercial Positions-Short (All)"]) / c["Open Interest (All)"]
    tests = {"cot sigue cambio 1 sem": lambda n: np.sign(n.diff()), "cot sigue cambio 4 sem": lambda n: np.sign(n.diff(4)),
             "cot sigue nivel": lambda n: np.sign(n),
             "cot contrario extremos z>1,5 (3 años)": lambda n: -np.sign(((n - n.rolling(156).mean()) / n.rolling(156).std()).where(lambda z: z.abs() > 1.5)),
             "cot sigue extremos z>1,5 (3 años)": lambda n: np.sign(((n - n.rolling(156).mean()) / n.rolling(156).std()).where(lambda z: z.abs() > 1.5))}
    for nm, f in tests.items():
        rows = []
        for s, (code, inv) in COTC.items():
            n = c[c.code == code].drop_duplicates("d").set_index("d").net.sort_index()
            sig = f(n) * inv
            d = PX[s]
            # dato del martes, publicado el viernes: se opera de la apertura del lunes siguiente al cierre del viernes
            wk = d.resample("W-FRI").agg({"Open": "first", "Close": "last"}).dropna()
            r = np.log(wk.Close / wk.Open); vol = r.rolling(36).std().shift(1); cost = T.COST[s] / wk.Open
            sg_w = sig.copy(); sg_w.index = sg_w.index + pd.Timedelta(days=10)   # martes -> viernes de la semana siguiente
            sg_w = sg_w.reindex(sg_w.index.union(wk.index)).ffill(limit=1).reindex(wk.index)
            for dt in wk.index:
                sg = sg_w.get(dt, np.nan)
                if not np.isfinite(sg) or sg == 0 or not np.isfinite(vol[dt]): continue
                rows.append((dt, (sg * r[dt] - cost[dt]) / vol[dt], (sg * r[dt] - 2 * cost[dt]) / vol[dt]))
        evaluate(nm, rows)

carry_tests(); cot_tests()
