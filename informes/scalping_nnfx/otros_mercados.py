# Prueba fuera de mercado de GER40 retroceso EMA20 (E1, G2, M30, sin filtro): las mismas reglas, sin cambiar nada,
# en otros índices a su hora de apertura y en los pares de forex con M1 en el PC a la apertura de Londres.
# Hora servidor NY+7. Japón y Hong Kong no cambian de hora: su apertura en hora servidor se mueve con el DST de EE. UU.
# Uso: python3 otros_mercados.py DIR_M1 SALIDA
import sys, os, numpy as np, pandas as pd
src = open(__file__.replace("otros_mercados.py", "coste_bajo.py")).read().split("rows, trades = [], []")[0]
src = src.replace("@njit(cache=True)", "@njit").replace('MK = {', 'MK_OLD = {')
exec(src)
FX = 0.6
# nombre: (ficheros [(fichero, factor spread, desde, hasta)], comisión, inicio, fin de sesión en min servidor, desplaza con DST EE. UU.)
M = {
    "GER40":  ([("DEUIDXEUR_M1_DUKA.csv", 1.0, None, "2022-01-01"), ("GER40_M1_FTMO.csv", 1.0, "2022-01-01", None)], 0, 600, 1105, False),
    "FRA40":  ([("FRAIDXEUR_M1_DUKA.csv", 1.0, None, None)], 0, 600, 1105, False),
    "EU50":   ([("EUSIDXEUR_M1_DUKA.csv", 1.0, None, None)], 0, 600, 1105, False),
    "ESP35":  ([("ESPIDXEUR_M1_DUKA.csv", 1.0, None, None)], 0, 600, 1105, False),
    "NLD25":  ([("NLDIDXEUR_M1_DUKA.csv", 1.0, None, None)], 0, 600, 1105, False),
    "UK100":  ([("GBRIDXGBP_M1_DUKA.csv", 1.0, None, None)], 0, 600, 1105, False),
    "US100":  ([("US100_M1_DUKA_2018_2022.csv", 0.01, None, "2023-01-01"), ("US100_cash_M1_FTMO.csv", 0.01, "2023-01-01", None)], 0, 990, 1375, False),
    "US500":  ([("USA500IDXUSD_M1_DUKA.csv", 1.0, None, None)], 0, 990, 1375, False),
    "US30":   ([("USA30IDXUSD_M1_DUKA.csv", 1.0, None, None)], 0, 990, 1375, False),
    "US2000": ([("USSC2000IDXUSD_M1_DUKA.csv", 1.0, None, None)], 0, 990, 1375, False),
    "JP225":  ([("JPNIDXJPY_M1_DUKA.csv", 1.0, None, None)], 0, 120, 505, True),    # 09:00 JST = 02:00 servidor en invierno
    "HK50":   ([("HKGIDXHKD_M1_DUKA.csv", 1.0, None, None)], 0, 210, 595, True),    # 09:30 HKT = 03:30 servidor en invierno
    "EURUSD": ([("EURUSD_M1_DUKA.csv", 1.0, None, None)], FX * 1e-4, 600, 1105, False),
    "GBPUSD": ([("GBPUSD_M1_DUKA.csv", 1.0, None, None)], FX * 1e-4, 600, 1105, False),
    "USDJPY": ([("USDJPY_M1_DUKA.csv", 1.0, None, None)], FX * 1e-2, 600, 1105, False),
}

def load2(sym):
    cache = f"{OUT}/{sym}.pkl"
    if os.path.exists(cache): return pd.read_pickle(cache)
    parts = []
    for f, fsp, a, b in M[sym][0]:
        d = pd.read_csv(f"{DIR}/{f}", usecols=["time", "open", "high", "low", "close", "spread"], parse_dates=["time"])
        if a: d = d[d.time >= a]
        if b: d = d[d.time < b]
        d["spread"] = d.spread * fsp; parts.append(d)
    d = pd.concat(parts).sort_values("time").drop_duplicates("time")
    d = d[d.time >= "2018-01-01"].reset_index(drop=True); d.to_pickle(cache); return d

def us_dst(t):   # horario de verano de EE. UU. (2.º domingo de marzo a 1.er domingo de noviembre)
    y = t.dt.year; m = t.dt.month; dd = t.dt.day; wd = t.dt.weekday
    first_sun = lambda yy, mm: pd.to_datetime(dict(year=yy, month=mm, day=1)) + pd.to_timedelta((6 - pd.to_datetime(dict(year=yy, month=mm, day=1)).dt.weekday) % 7, "D")
    start = first_sun(y, 3) + pd.Timedelta(days=7); end = first_sun(y, 11)
    return (t >= start) & (t < end)

def caso(d, sym, sm=1.0, seed=None, tf=30, win=90):
    files, comm, w0, s1, shift = M[sym]
    o, h, l, c, sp = (d[x].values.astype(float) for x in ["open", "high", "low", "close", "spread"])
    tod = (d.time.dt.hour * 60 + d.time.dt.minute).values
    if shift: tod = tod - 60 * us_dst(d.time).values.astype(int)       # hora local fija
    day = d.time.dt.normalize().values; dayid = pd.factorize(day)[0].astype(np.int64)
    insess = (tod >= w0) & (tod < s1); idx = np.where(insess)[0]
    send = np.zeros(len(d), bool); send[pd.Series(idx, index=day[idx]).groupby(level=0).max().values] = True
    B = bars(d, tf); pl = np.searchsorted(d.time.values, B["last"].values)
    tfend = np.zeros(len(d), bool); tfend[pl] = True
    Am = np.zeros(len(d)); Am[pl] = B.A.fillna(0).values
    S = np.where((B.e50 > B.e200) & (B.l <= B.e20) & (B.c > B.e20) & (B.c > B.o), 1,
                 np.where((B.e50 < B.e200) & (B.h >= B.e20) & (B.c < B.e20) & (B.c < B.o), -1, 0))
    if seed is not None: S = np.where(S != 0, np.where(np.random.default_rng(seed).random(len(S)) < 0.5, 1, -1), 0)
    sig = np.zeros(len(d), np.int64); sig[pl] = S
    okw = np.zeros(len(d), bool); okw[pl] = (tod[pl] + 1 >= w0 + tf) & (tod[pl] + 1 <= w0 + win); sig[~(okw & insess)] = 0
    # la comisión se suma al spread de cada minuto (se paga en la entrada)
    ti, te, tR, tc = run(o, h, l, c, sp + comm, tfend, sig, Am, send, dayid, sm, 2, 2)
    return pd.DataFrame(dict(t=d.time.values[ti], R=tR, c=tc))

def st(X):
    a, b = X[X.t < "2023-01-01"].R, X[X.t >= "2023-01-01"].R
    yr = X.groupby(X.t.dt.year).R.mean()
    return dict(ops_año=len(X) / ((X.t.max() - X.t.min()).days / 365.25), aj=a.mean(), t_aj=tstat(a), pr=b.mean(), t_pr=tstat(b),
                años_pos=f"{(yr > 0).sum()}/{len(yr)}", coste=X.c.mean())

rows, allT = [], []
for sym in M:
    d = load2(sym)
    X = caso(d, sym); X2 = caso(d, sym, sm=2.0)
    P = [st(caso(d, sym, seed=s)) for s in range(20)]
    r = dict(mercado=sym, **st(X), pr_x2=st(X2)["pr"], aj_x2=st(X2)["aj"],
             plac_aj=np.mean([p["aj"] for p in P]), plac_aj95=np.quantile([p["aj"] for p in P], .95),
             plac_pr=np.mean([p["pr"] for p in P]), plac_pr95=np.quantile([p["pr"] for p in P], .95))
    rows.append(r); allT.append(X.assign(sym=sym)); print(r, flush=True)
R = pd.DataFrame(rows); R.to_csv(f"{OUT}/otros_mercados.csv", index=False)
pd.concat(allT).to_csv(f"{OUT}/otros_mercados_trades.csv", index=False)
pd.set_option("display.width", 250); print(R.round(3).to_string(index=False))
