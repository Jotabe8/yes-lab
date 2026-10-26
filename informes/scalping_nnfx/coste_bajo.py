# Scalping de coste bajo: las cuatro palancas para que el spread pese poco (pre-registro 2026-10-26, antes de ver datos).
#   Mercados: US100 (Dukascopy 2018-22, FTMO 2023-26) y GER40 (Dukascopy 2018-21, FTMO 2022-26). Hora servidor NY+7.
#   Temporalidades: M15 y M30. ATR(14) de la temporalidad.
#   Ventana de entrada: primera hora y media de contado (US100 16:30-18:00, GER40 10:00-11:30). La posición puede
#   seguir hasta el final de la sesión (US100 22:55, GER40 18:25), donde se cierra. Máximo 2 operaciones por día y mercado.
#   Filtro de coste: solo se entra si (spread del minuto de señal + comisión) / (1,5 ATR) <= 0,02.
#   Gestiones: G1 NNFX de VP (SL 1,5 ATR, mitad a 1 ATR, BE, trailing 2 ATR al cierre de vela);
#              G2 corredor (SL 1,5 ATR, a BE al llegar a +1 ATR, sin parcial, trailing 2 ATR).
#   Entradas: R0 aleatoria (placebo, 20 repeticiones), E1 retroceso a EMA20 con tendencia, E2 ruptura Donchian 20
#             a favor de la EMA200, E3 RSI(2) extremo a favor de la EMA200.
#   Criterio: neto > 0 en ajuste (2018-22) y prueba (2023-26), t >= 2 en prueba, neto > 0 con costes al doble,
#             por encima del percentil 95 del placebo en prueba. Solo entonces EV por cuota FTMO.
# Uso: python3 coste_bajo.py DIR_M1 SALIDA
import sys, os, numpy as np, pandas as pd
from numba import njit

DIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
MK = {  # ficheros (hasta, desde), factor de spread, ventana de señal, fin de sesión (minutos servidor)
    "US100": ([("US100_M1_DUKA_2018_2022.csv", 0.01, None, "2023-01-01"), ("US100_cash_M1_FTMO.csv", 0.01, "2023-01-01", None)], 990, 1080, 1375),
    "GER40": ([("DEUIDXEUR_M1_DUKA.csv", 1.0, None, "2022-01-01"), ("GER40_M1_FTMO.csv", 1.0, "2022-01-01", None)], 600, 690, 1105),
}
TFS, MAXC, REPS = [15, 30], 0.02, 20

def load(sym):
    cache = f"{OUT}/{sym}.pkl"
    if os.path.exists(cache): return pd.read_pickle(cache)
    parts = []
    for f, fsp, a, b in MK[sym][0]:
        d = pd.read_csv(f"{DIR}/{f}", usecols=["time", "open", "high", "low", "close", "spread"], parse_dates=["time"])
        if a: d = d[d.time >= a]
        if b: d = d[d.time < b]
        d["spread"] = d.spread * fsp; parts.append(d)
    d = pd.concat(parts).sort_values("time").drop_duplicates("time")
    d = d[d.time >= "2018-01-01"].reset_index(drop=True); d.to_pickle(cache); return d

@njit(cache=True)
def run(o, h, l, c, sp, tfend, sig, A, send, dayid, smult, mode, maxday):
    n = len(c); out_i = np.full(n, -1); out_e = np.full(n, -1); out_R = np.zeros(n); out_c = np.zeros(n); k = 0
    i = 0; cur = -1; cnt = 0
    while i < n - 1:
        if dayid[i] != cur: cur = dayid[i]; cnt = 0
        if sig[i] != 0 and not send[i] and A[i] > 0 and cnt < maxday:
            pos = sig[i]; j = i + 1; cnt += 1
            ent = o[j] + (sp[j] * smult if pos == 1 else 0.0)
            risk = 1.5 * A[i]; sl = ent - pos * risk; tp1 = ent + pos * A[i]
            w = 1.0; done1 = False; R = 0.0; i0 = j
            while j < n:
                a = sp[j] * smult if pos == -1 else 0.0
                lo = l[j] + a; hi = h[j] + a
                if (pos == 1 and lo <= sl) or (pos == -1 and hi >= sl):
                    px = sl if j == i0 else (min(o[j] + a, sl) if pos == 1 else max(o[j] + a, sl))
                    R += w * pos * (px - ent) / risk; w = 0.0; break
                if not done1 and ((pos == 1 and hi >= tp1) or (pos == -1 and lo <= tp1)):
                    done1 = True; sl = ent
                    if mode == 1: R += 0.5 * pos * (tp1 - ent) / risk; w = 0.5
                if send[j]:
                    R += w * pos * (c[j] + a - ent) / risk; w = 0.0; break
                if done1 and tfend[j] and A[j] > 0:
                    ns = c[j] + a - pos * 2.0 * A[j]
                    if pos * (ns - sl) > 0: sl = ns
                j += 1
            out_i[k] = i0; out_e[k] = j; out_R[k] = R; out_c[k] = sp[i0] * smult / risk; k += 1
            i = j; continue
        i += 1
    return out_i[:k], out_e[:k], out_R[:k], out_c[:k]

def ema(x, n): return x.ewm(span=n, adjust=False).mean()

def bars(d, tf):
    B = d.groupby(d.time.dt.floor(f"{tf}min")).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"),
                                                   c=("close", "last"), last=("time", "last"))
    pc = B.c.shift(); tr = pd.concat([B.h - B.l, (B.h - pc).abs(), (B.l - pc).abs()], axis=1).max(axis=1)
    B["A"] = tr.rolling(14).mean(); B["e20"], B["e50"], B["e200"] = ema(B.c, 20), ema(B.c, 50), ema(B.c, 200)
    g = B.c.diff(); w = lambda x: x.ewm(alpha=1 / 2, adjust=False).mean()
    B["rsi2"] = 100 - 100 / (1 + w(g.clip(lower=0)) / w(-g.clip(upper=0)).replace(0, np.nan))
    B["dh"], B["dl"] = B.h.shift(1).rolling(20).max(), B.l.shift(1).rolling(20).min()
    return B

def signals(B, name, rng):
    up, dn = B.c > B.e200, B.c < B.e200
    if name == "R0": return np.where(rng.random(len(B)) < 0.5, 1, -1)
    if name == "E1": return np.where((B.e50 > B.e200) & (B.l <= B.e20) & (B.c > B.e20) & (B.c > B.o), 1,
                                     np.where((B.e50 < B.e200) & (B.h >= B.e20) & (B.c < B.e20) & (B.c < B.o), -1, 0))
    if name == "E2": return np.where(up & (B.c > B.dh), 1, np.where(dn & (B.c < B.dl), -1, 0))
    if name == "E3": return np.where(up & (B.rsi2 < 10), 1, np.where(dn & (B.rsi2 > 90), -1, 0))

def tstat(x): x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan

rows, trades = [], []
for sym in MK:
    d = load(sym); w0, w1, s1 = MK[sym][1], MK[sym][2], MK[sym][3]
    o, h, l, c, sp = (d[x].values.astype(float) for x in ["open", "high", "low", "close", "spread"])
    tod = (d.time.dt.hour * 60 + d.time.dt.minute).values
    day = d.time.dt.normalize().values; dayid = pd.factorize(day)[0].astype(np.int64)
    insess = (tod >= w0) & (tod < s1); idx = np.where(insess)[0]
    send = np.zeros(len(d), bool); send[pd.Series(idx, index=day[idx]).groupby(level=0).max().values] = True
    send[~insess] = False
    for tf in TFS:
        B = bars(d, tf); pl = np.searchsorted(d.time.values, B["last"].values)
        tfend = np.zeros(len(d), bool); tfend[pl] = True
        Am = np.zeros(len(d)); Am[pl] = B.A.fillna(0).values
        win = np.zeros(len(d), bool); win[pl] = (tod[pl] + 1 >= w0 + tf) & (tod[pl] + 1 <= w1)   # vela cerrada dentro de la ventana
        cheap = np.zeros(len(d), bool); ok = Am[pl] > 0
        cheap[pl[ok]] = sp[pl[ok]] / (1.5 * Am[pl[ok]]) <= MAXC
        for name in ["R0", "E1", "E2", "E3"]:
            for rep in range(REPS if name == "R0" else 1):
                S = signals(B, name, np.random.default_rng(500 + rep))
                for filt in [1, 0]:
                    sig = np.zeros(len(d), np.int64); sig[pl] = S; sig[~(win & insess)] = 0
                    if filt: sig[~cheap] = 0
                    for mode in [1, 2]:
                        res = {}
                        for sm in [0.0, 1.0, 2.0]:
                            ti, te, tR, tc = run(o, h, l, c, sp, tfend, sig, Am, send, dayid, sm, mode, 2)
                            res[sm] = pd.DataFrame(dict(t=d.time.values[ti], R=tR, c=tc))
                        if name != "R0" or rep < 5:
                            for sm in [1.0, 2.0]:
                                trades.append(res[sm].assign(sym=sym, tf=tf, entrada=name, filtro=filt, gestion=f"G{mode}", rep=rep, costes=sm))
                        for per, a, b in [("2018-22", "2018", "2022-12-31 23:59"), ("2023-26", "2023", "2027")]:
                            r = {sm: x[(x.t >= a) & (x.t <= b)] for sm, x in res.items()}
                            yrs = (min(pd.Timestamp(b), d.time.max()) - pd.Timestamp(a)).days / 365.25
                            rows.append(dict(sym=sym, tf=tf, entrada=name, filtro=filt, gestion=f"G{mode}", rep=rep, periodo=per,
                                             ops_año=len(r[1.0]) / yrs, bruto=r[0.0].R.mean(), neto=r[1.0].R.mean(), neto2=r[2.0].R.mean(),
                                             coste_R=r[1.0].c.mean(), t_neto=tstat(r[1.0].R), acierto=(r[1.0].R > 0).mean() * 100))
            print(sym, tf, name, "hecho", flush=True)
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/cb_resumen.csv", index=False)
pd.concat(trades).to_pickle(f"{OUT}/cb_trades.pkl")
K = ["sym", "tf", "entrada", "filtro", "gestion", "periodo"]
G = D[D.entrada != "R0"].drop(columns="rep")
P = D[D.entrada == "R0"].groupby(K).agg(neto=("neto", "mean"), p95=("neto", lambda s: s.quantile(.95)), bruto=("bruto", "mean"),
                                        coste_R=("coste_R", "mean"), ops_año=("ops_año", "mean"), t_neto=("t_neto", "mean")).reset_index()
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 1000)
print("PLACEBO R0 (media de 20 repeticiones, p95 del neto)"); print(P.round(3).to_string(index=False))
print("ENTRADAS"); print(G.round(3).to_string(index=False))
P.to_csv(f"{OUT}/cb_placebo.csv", index=False)
