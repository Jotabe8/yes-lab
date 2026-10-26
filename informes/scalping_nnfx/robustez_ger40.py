# Robustez de la única casilla que pasó el pre-registro de coste_bajo.py: GER40 M30, retroceso a EMA20 con
# tendencia (E1), gestión corredor (G2), sin filtro de coste. Se mueve un parámetro cada vez alrededor del original.
# Uso: python3 robustez_ger40.py DIR_M1 SALIDA
import sys, numpy as np, pandas as pd
src = open(__file__.replace("robustez_ger40.py", "coste_bajo.py")).read().split("rows, trades = [], []")[0]
exec(src.replace("@njit(cache=True)", "@njit"))
d = load("GER40")
o, h, l, c, sp = (d[x].values.astype(float) for x in ["open", "high", "low", "close", "spread"])
tod = (d.time.dt.hour * 60 + d.time.dt.minute).values
day = d.time.dt.normalize().values; dayid = pd.factorize(day)[0].astype(np.int64)

def caso(tf=30, efast=20, emid=50, eslow=200, win=90, maxday=2, mode=2, trend=True, sm=1.0, seed=None, ret=False):
    w0, s1 = 600, 1105; w1 = w0 + win
    insess = (tod >= w0) & (tod < s1); idx = np.where(insess)[0]
    send = np.zeros(len(d), bool); send[pd.Series(idx, index=day[idx]).groupby(level=0).max().values] = True
    B = bars(d, tf); B["ef"] = ema(B.c, efast); B["em"] = ema(B.c, emid); B["es"] = ema(B.c, eslow)
    pl = np.searchsorted(d.time.values, B["last"].values)
    tfend = np.zeros(len(d), bool); tfend[pl] = True
    Am = np.zeros(len(d)); Am[pl] = B.A.fillna(0).values
    up = (B.em > B.es) if trend else np.ones(len(B), bool); dn = (B.em < B.es) if trend else np.ones(len(B), bool)
    S = np.where(up & (B.l <= B.ef) & (B.c > B.ef) & (B.c > B.o), 1, np.where(dn & (B.h >= B.ef) & (B.c < B.ef) & (B.c < B.o), -1, 0))
    if seed is not None:   # placebo: mismas velas de señal, dirección aleatoria
        S = np.where(S != 0, np.where(np.random.default_rng(seed).random(len(S)) < 0.5, 1, -1), 0)
    sig = np.zeros(len(d), np.int64); sig[pl] = S
    okw = np.zeros(len(d), bool); okw[pl] = (tod[pl] + 1 >= w0 + tf) & (tod[pl] + 1 <= w1); sig[~(okw & insess)] = 0
    ti, te, tR, tc = run(o, h, l, c, sp, tfend, sig, Am, send, dayid, sm, mode, maxday)
    X = pd.DataFrame(dict(t=d.time.values[ti], R=tR, c=tc))
    if ret: return X
    a, b = X[X.t < "2023-01-01"].R, X[X.t >= "2023-01-01"].R
    yr = X.groupby(X.t.dt.year).R.mean()
    return dict(n_año=len(X) / 8.8, aj=a.mean(), t_aj=tstat(a), pr=b.mean(), t_pr=tstat(b), años_pos=f"{(yr > 0).sum()}/{len(yr)}", coste=X.c.mean())

rows = [dict(caso="ORIGINAL M30 EMA20/50/200 ventana 90 máx 2 G2", **caso())]
rows.append(dict(caso="costes x2", **caso(sm=2.0)))
rows.append(dict(caso="gestión G1 (NNFX VP)", **caso(mode=1)))
for tf in [15, 20, 60]: rows.append(dict(caso=f"TF M{tf}", **caso(tf=tf)))
for ef in [10, 30, 50]: rows.append(dict(caso=f"EMA rápida {ef}", **caso(efast=ef)))
for es in [100, 400]: rows.append(dict(caso=f"EMA lenta {es}", **caso(eslow=es)))
rows.append(dict(caso="sin filtro de tendencia", **caso(trend=False)))
for w in [60, 120, 180]: rows.append(dict(caso=f"ventana {w} min", **caso(win=w)))
for m in [1, 3]: rows.append(dict(caso=f"máx {m} ops/día", **caso(maxday=m)))
R = pd.DataFrame(rows)
pl = pd.DataFrame([caso(seed=s) for s in range(50)])
pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False))
print("PLACEBO dirección aleatoria en las mismas velas (50): prueba media %.3f p95 %.3f | ajuste media %.3f p95 %.3f"
      % (pl.pr.mean(), pl.pr.quantile(.95), pl.aj.mean(), pl.aj.quantile(.95)))
R.to_csv(f"{OUT}/robustez_ger40.csv", index=False)
caso(ret=True).to_csv(f"{OUT}/ger40_e1_trades.csv", index=False)
