# Estacionalidad de calendario en forex y oro (D1 limpios). Señal sin mirar al futuro:
# para el mes m del año y, dirección = signo de la media del retorno del mes m en los K años previos.
# Se mantiene todo el mes (entra a la apertura del primer día, sale al cierre del último). Coste 1 spread ida y vuelta, y al doble.
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/mnt/project-files/ea-pons-nnfx"); import torneo_vp as T
D = {}
for s in T.SYMS:
    x = pd.read_csv(f"/tmp/claude-0/mt5/{s}_D1.csv"); x["Date"] = pd.to_datetime(x.Date.str.replace(".", "-"))
    D[s] = x.set_index("Date")[["Open", "Close"]]
res = {}
for K in (5, 10, 15):
    rows = []
    for s, d in D.items():
        m = d.resample("ME").agg({"Open": "first", "Close": "last"}).dropna()
        r = np.log(m.Close / m.Open); cost = T.COST[s] / m.Open
        for i, (dt, ri) in enumerate(r.items()):
            past = r[(r.index.month == dt.month) & (r.index.year < dt.year) & (r.index.year >= dt.year - K)]
            if len(past) < K: continue
            sg = np.sign(past.mean()); sd = r.iloc[max(0, i - 36):i].std()
            rows.append(dict(s=s, dt=dt, R=(sg * ri - cost.iloc[i]) / sd, R2=(sg * ri - 2 * cost.iloc[i]) / sd))
    df = pd.DataFrame(rows); res[K] = df
    for a, b in (("2010", "2016"), ("2017", "2026")):
        q = df[(df.dt >= a) & (df.dt <= b + "-12-31")]
        t = q.R2.mean() / q.R2.std() * np.sqrt(len(q))
        print(f"K={K} {a}-{b}: n {len(q)} media {q.R2.mean():+.3f} (unid. vol mensual) t {t:+.2f} | años+ {(q.groupby(q.dt.dt.year).R2.mean() > 0).mean():.0%}")
