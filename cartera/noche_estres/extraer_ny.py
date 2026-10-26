import sys, pandas as pd
par = sys.argv[1]
out = []
for ch in pd.read_csv(f"../../data/{par}_M1_DUKA.csv", chunksize=800_000):
    t = pd.to_datetime(ch.time) - pd.Timedelta(hours=7)   # hora servidor = NY+7
    m = t.dt.hour.between(7, 16)
    w = ch[m.values].copy(); w["ny"] = t[m].values
    out.append(w.drop(columns="time"))
v = pd.concat(out).set_index("ny").sort_index()
v = v[~v.index.duplicated()]
v.to_pickle(f"ny_{par}.pkl"); print(par, len(v), v.index.min(), v.index.max())
