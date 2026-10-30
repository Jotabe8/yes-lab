# Control: misma regla sobre futuros (precios negociables) frente al índice de contado de Yahoo.
import sys, numpy as np, pandas as pd
sys.argv = ["x"]
exec(open("nr7.py").read().split("rng = np.random")[0])
for f in ("ES_FUT", "NQ_FUT", "YM_FUT", "RTY_FUT"): SPR[f] = 0.0002
pares = [("US500", "ES_FUT"), ("US100", "NQ_FUT"), ("US30", "YM_FUT"), ("US2000", "RTY_FUT")]
filas = []
for cont, fut in pares:
    for s in (cont, fut):
        d = cargar(s); rg = d.high - d.low
        for var, f in [("NR7", rg == rg.rolling(7).min()), ("todos", pd.Series(True, d.index))]:
            x = operar(d, s).assign(senal=f.shift(1, fill_value=False).values).dropna(subset=["r_bruto"])
            x = x[np.isfinite(x.r_bruto) & (x.coste_r < 1) & x.senal & (x.index >= "2002-06-01") & (x.index <= "2022-12-31")]
            if s == "RTY_FUT" or cont == "US2000": x = x[x.index >= "2017-08-01"]
            n = x.r_bruto - x.coste_r
            filas.append(dict(serie=s, var=var, ops=len(n), bruto=x.r_bruto.mean(), neto=n.mean(),
                              t=n.mean() / n.std() * np.sqrt(len(n))))
print(pd.DataFrame(filas).round(3).to_string(index=False))
