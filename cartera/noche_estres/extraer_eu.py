import sys, pandas as pd
nom, ruta, desf = sys.argv[1], sys.argv[2], int(sys.argv[3])   # desf: horas a restar para pasar a CET
out = []
for ch in pd.read_csv(ruta, chunksize=1_500_000):
    t = pd.to_datetime(ch.time) - pd.Timedelta(hours=desf)
    m = t.dt.hour.isin([8, 9, 20, 21, 22])
    w = ch[m.values].copy(); w["cet"] = t[m].values
    out.append(w[["cet", "open", "high", "low", "close", "spread"]])
v = pd.concat(out).set_index("cet").sort_index(); v = v[~v.index.duplicated()]
v.to_pickle(f"eu_{nom}.pkl"); print(nom, len(v), v.index.min(), v.index.max())
