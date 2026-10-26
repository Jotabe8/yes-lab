# Scalping con gestión de riesgo NNFX sobre velas M1 bid + spread (Dukascopy / FTMO), hora servidor = NY+7.
# Pre-registro (2026-10-26, antes de ver resultados):
#   Temporalidades M1, M5, M15. Solo en sesión líquida; todo se cierra al final de la sesión (sin swap).
#   Gestión NNFX: SL 1,5 ATR(14) de la temporalidad, mitad a 1 ATR, resto a BE y trailing de 2 ATR al cierre de vela.
#   Entradas (señal al cierre de la vela, entrada a la apertura del minuto siguiente, una posición por mercado):
#     R0 aleatoria (placebo: moneda en cada cierre de vela estando fuera)
#     E1 retroceso a EMA20 con tendencia (EMA50 > EMA200, el mínimo toca la EMA20 y cierra por encima, vela alcista)
#     E2 ruptura Donchian de 20 velas a favor de la EMA200
#     E3 RSI(2) < 10 a favor de la EMA200 (compra la caída en tendencia; simétrico en cortos)
#   Ajuste 2018-2022, prueba 2023-2026. Vale solo si: neto > 0 en ajuste y prueba, t >= 2 en prueba,
#   neto > 0 con costes al doble y mejor que R0 en la misma temporalidad y mercado.
# Uso: python3 scalping.py DIR_M1 SALIDA
import sys, os, numpy as np, pandas as pd
from numba import njit

DIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
IS_END, OOS = "2022-12-31", "2023-01-01"
# mercado: ficheros, factor del spread, comisión ida y vuelta en precio, sesión (min servidor desde 00:00)
FXC = 0.6  # pips de comisión FTMO (3 $/lote por lado)
MK = {
    "EURUSD": (["EURUSD_M1_DUKA.csv"], 1.0, FXC * 1e-4, 600, 1140),
    "GBPUSD": (["GBPUSD_M1_DUKA.csv"], 1.0, FXC * 1e-4, 600, 1140),
    "USDJPY": (["USDJPY_M1_DUKA.csv"], 1.0, FXC * 1e-2, 600, 1140),
    "XAUUSD": (["XAUUSD_M1_DUKA.csv"], 1.0, 0.0, 600, 1140),
    "US100":  (["US100_M1_DUKA_2018_2022.csv", "US100_cash_M1_FTMO.csv"], 0.01, 0.0, 990, 1375),
    "US500":  (["USA500IDXUSD_M1_DUKA.csv"], 1.0, 0.0, 990, 1375),
    "GER40":  (["GER40_M1_FTMO.csv"], 1.0, 0.0, 600, 1105),
}
TFS = [1, 5, 15]

def load(sym):
    cache = f"{OUT}/{sym}.pkl"
    if os.path.exists(cache): return pd.read_pickle(cache)
    files, fsp = MK[sym][0], MK[sym][1]
    parts = []
    for k, f in enumerate(files):
        d = pd.read_csv(f"{DIR}/{f}", usecols=["time", "open", "high", "low", "close", "spread"], parse_dates=["time"])
        if sym == "US100": d = d[d.time < "2023-01-01"] if k == 0 else d[d.time >= "2023-01-01"]
        parts.append(d)
    d = pd.concat(parts).sort_values("time").drop_duplicates("time")
    d["spread"] = d.spread * fsp
    d = d[d.time >= "2018-01-01"].reset_index(drop=True)
    d.to_pickle(cache); return d

@njit(cache=True)
def run(o, h, l, c, sp, tfend, sig, A, send, smult, comm, nnfx):
    # sig[i] != 0 en el último minuto de una vela TF; A[i] = ATR de esa vela; send[i] = último minuto de la sesión
    n = len(c); out_i = np.full(n, -1); out_R = np.zeros(n); out_c = np.zeros(n); k = 0
    pos = 0; i = 0
    while i < n - 1:
        if pos == 0:
            if sig[i] != 0 and not send[i] and A[i] > 0:
                pos = sig[i]; j = i + 1
                ent = o[j] + (sp[j] * smult if pos == 1 else 0.0)
                risk = 1.5 * A[i]; sl = ent - pos * risk; tp1 = ent + pos * 1.0 * A[i]
                w = 1.0; done1 = False; R = -comm * smult / risk; cst = (sp[j] * smult + comm * smult) / risk; i0 = j
                while j < n:
                    a = sp[j] * smult if pos == -1 else 0.0       # largo sale al bid; corto al ask
                    lo = l[j] + a; hi = h[j] + a
                    if (pos == 1 and lo <= sl) or (pos == -1 and hi >= sl):
                        px = min(o[j] + a, sl) if pos == 1 else max(o[j] + a, sl)
                        if j == i0: px = sl
                        R += w * pos * (px - ent) / risk; w = 0.0; break
                    if nnfx and not done1 and ((pos == 1 and hi >= tp1) or (pos == -1 and lo <= tp1)):
                        R += 0.5 * pos * (tp1 - ent) / risk; w = 0.5; done1 = True; sl = ent
                    if not nnfx:   # 1:1 de control: TP a 1,5 ATR (= riesgo)
                        tp = ent + pos * risk
                        if (pos == 1 and hi >= tp) or (pos == -1 and lo <= tp):
                            R += w * pos * (tp - ent) / risk; w = 0.0; break
                    if send[j]:
                        R += w * pos * (c[j] + a - ent) / risk; w = 0.0; break
                    if nnfx and done1 and tfend[j] and A[j] > 0:
                        ns = c[j] + a - pos * 2.0 * A[j]
                        if pos * (ns - sl) > 0: sl = ns
                    j += 1
                out_i[k] = i0; out_R[k] = R; out_c[k] = cst; k += 1
                pos = 0; i = j          # puede volver a entrar en la señal del mismo minuto de salida
                continue
        i += 1
    return out_i[:k], out_R[:k], out_c[:k]

def ema(x, n): return x.ewm(span=n, adjust=False).mean()

def bars(d, tf, s0, s1):
    t = d.time; tod = t.dt.hour * 60 + t.dt.minute
    insess = (tod >= s0) & (tod < s1)
    key = t.dt.floor(f"{tf}min")
    B = d.groupby(key).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), last=("time", "last"))
    pc = B.c.shift(); tr = pd.concat([B.h - B.l, (B.h - pc).abs(), (B.l - pc).abs()], axis=1).max(axis=1)
    B["A"] = tr.rolling(14).mean()
    B["e20"], B["e50"], B["e200"] = ema(B.c, 20), ema(B.c, 50), ema(B.c, 200)
    g = B.c.diff(); w = lambda x: x.ewm(alpha=1 / 2, adjust=False).mean()
    B["rsi2"] = 100 - 100 / (1 + w(g.clip(lower=0)) / w(-g.clip(upper=0)).replace(0, np.nan))
    B["dh"], B["dl"] = B.h.shift(1).rolling(20).max(), B.l.shift(1).rolling(20).min()
    return B, insess.values, tod.values

def signals(B, rng):
    up, dn = B.c > B.e200, B.c < B.e200
    S = {}
    S["R0"] = np.where(rng.random(len(B)) < 0.5, 1, -1)
    S["E1"] = np.where((B.e50 > B.e200) & (B.l <= B.e20) & (B.c > B.e20) & (B.c > B.o), 1,
              np.where((B.e50 < B.e200) & (B.h >= B.e20) & (B.c < B.e20) & (B.c < B.o), -1, 0))
    S["E2"] = np.where(up & (B.c > B.dh), 1, np.where(dn & (B.c < B.dl), -1, 0))
    S["E3"] = np.where(up & (B.rsi2 < 10), 1, np.where(dn & (B.rsi2 > 90), -1, 0))
    return S

def tstat(x): x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan

rows = []
for sym in MK:
    d = load(sym); s0, s1 = MK[sym][3], MK[sym][4]
    o, h, l, c, sp = (d[x].values.astype(float) for x in ["open", "high", "low", "close", "spread"])
    tod = (d.time.dt.hour * 60 + d.time.dt.minute).values
    insess = (tod >= s0) & (tod < s1)
    day = d.time.dt.normalize().values
    # último minuto de sesión de cada día (o último minuto disponible del día dentro de la sesión)
    idx = np.where(insess)[0]
    last_of_day = pd.Series(idx, index=day[idx]).groupby(level=0).max().values
    send = np.zeros(len(d), bool); send[last_of_day] = True
    for tf in TFS:
        B, _, _ = bars(d, tf, s0, s1)
        pos_last = np.searchsorted(d.time.values, B["last"].values)   # índice M1 del cierre de cada vela
        tfend = np.zeros(len(d), bool); tfend[pos_last] = True
        Am = np.zeros(len(d)); Am[pos_last] = B.A.fillna(0).values
        for name in ["R0", "E1", "E2", "E3"]:
            for nn in [1, 0] if name == "R0" else [1]:
                for rep in range(5 if name == "R0" else 1):
                    S = signals(B, np.random.default_rng(100 + rep))[name]
                    sig = np.zeros(len(d), np.int64); sig[pos_last] = S
                    sig[~insess] = 0
                    res = {}
                    for sm in [0.0, 1.0, 2.0]:
                        ti, tR, tc = run(o, h, l, c, sp, tfend, sig, Am, send, sm, MK[sym][2], bool(nn))
                        res[sm] = pd.DataFrame(dict(t=d.time.values[ti], R=tR, c=tc))
                    for per, a, b in [("2018-22", "2018", IS_END), ("2023-26", OOS, "2027")]:
                        r = {sm: x[(x.t >= a) & (x.t <= b)] for sm, x in res.items()}
                        yrs = (pd.Timestamp(min(b, str(d.time.max()))) - pd.Timestamp(a)).days / 365.25
                        rows.append(dict(sym=sym, tf=tf, entrada=name if nn else "R0 1:1", rep=rep, periodo=per,
                                         ops_año=len(r[1.0]) / yrs, bruto=r[0.0].R.mean(), neto=r[1.0].R.mean(),
                                         neto2=r[2.0].R.mean(), coste_R=r[1.0].c.mean(), t_neto=tstat(r[1.0].R),
                                         acierto=(r[1.0].R > 0).mean() * 100))
            print(sym, tf, name, "hecho", flush=True)
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/resumen.csv", index=False)
G = D.groupby(["sym", "tf", "entrada", "periodo"]).mean(numeric_only=True).drop(columns="rep").reset_index()
G.to_csv(f"{OUT}/resumen_medio.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 1000)
print(G.round(3).to_string(index=False))
