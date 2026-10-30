import numpy as np, pandas as pd, sys
sys.argv = ["x"]
exec(open("nr7.py").read().split("rng = np.random")[0])
D = {s: cargar(s) for s in SPR}
rows = []
for s, d in D.items():
    rg = d.high - d.low; f = (rg == rg.rolling(7).min()).shift(1, fill_value=False)
    x = operar(d, s).assign(senal=f.values).dropna(subset=["r_bruto"])
    x = x[np.isfinite(x.r_bruto) & (x.coste_r < 1)]; x["neto"] = x.r_bruto - x.coste_r
    x = x[(x.index >= "2000-01-01") & (x.index <= "2022-12-31")]
    per = pd.cut(x.index.year, [1999, 2007, 2015, 2022], labels=["00-07", "08-15", "16-22"])
    g = x.groupby([x.senal, per], observed=True).neto.mean().unstack()
    rows.append(pd.Series({f"{'NR7' if k else 'resto'} {p}": g.loc[k, p] for k in g.index for p in g.columns}, name=s))
print(pd.DataFrame(rows).round(3).to_string())
