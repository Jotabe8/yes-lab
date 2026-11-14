"""Réplica obligatoria candidato 1: misma regla V1 con el ETN VXX (corto) 2011-2026 y SVXY informativo."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))
def ind(n):
    d = pd.read_csv(D + f"{n}_History.csv"); d.columns = [c.upper() for c in d.columns]
    d["DATE"] = pd.to_datetime(d.DATE); return d.set_index("DATE").CLOSE
def yh(s):
    d = pd.read_csv(D + f"yahoo_{s}.csv", index_col=0, parse_dates=True)
    d = d[pd.to_numeric(d["Adj Close"], errors="coerce").notna()]
    return d["Adj Close"].astype(float)
ratio = ind("VIX") / ind("VIX3M")
for etf, signo in (("VXX", -1), ("SVXY", 1)):
    p = yh(etf); r = p.pct_change().dropna() * signo
    e = (ratio.reindex(r.index).ffill().shift(2) < 1).astype(float)
    net = e * r - e.diff().abs().fillna(0) * 0.0002 - (e * 0.05 / 252 if signo < 0 else 0)  # préstamo VXX ~5 %/año
    mitad = net.index[len(net) // 2]
    print(f"{etf} ({'corto' if signo<0 else 'largo'}) {net.index[0].date()}→{net.index[-1].date()}: anual {net.mean()*252:+.1%} vol {net.std()*np.sqrt(252):.1%} "
          f"t {t(net):.2f} | 1ª {net[:mitad].mean()*252:+.1%} 2ª {net[mitad:].mean()*252:+.1%} | siempre {r.mean()*252:+.1%} t {t(r):.2f}")
