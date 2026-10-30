# Prima de riesgo de índices en CFD (2026-10-26). Reglas fijadas antes de mirar:
# largo cuando el cierre > media de 200 sesiones (Faber 2007); tamaño por volatilidad (20 sesiones) para 10 % anual por mercado,
# palanca máx 2x; cartera equiponderada en riesgo. Financiación diaria = (tipo 3m + 2,5 %)/360 sobre el nominal (también +3,5 %).
# Spread 0,02 % del nominal por cambio de posición. Señal al cierre, posición desde el día siguiente.
import numpy as np, pandas as pd
M = "/home/claude/yes-lab/datos_macro/"
IDX = {"SP500": "US", "NDX": "US", "DJI": "US", "DAX": "EZ", "FTSE": "GB", "N225": "JP"}
def fred(sid):
    x = pd.read_csv(M + f"fred/{sid}.csv"); x.columns = ["d", "v"]; x["d"] = pd.to_datetime(x.d)
    return pd.to_numeric(x.v, errors="coerce").set_axis(x.d).dropna()
RATE = {c: fred(f"IR3TIB01{c}M156N") for c in set(IDX.values())}
def market(n, markup, filt=True, tv=0.10):
    d = pd.read_csv(M + f"indices/{n}.csv", parse_dates=["Date"]).set_index("Date")
    c = d.Close.astype(float).dropna(); c = c[c > 0]; r = c.pct_change()
    rate = RATE[IDX[n]].reindex(RATE[IDX[n]].index.union(c.index)).ffill().reindex(c.index) / 100
    fin = (rate + markup) / 360 * c.index.to_series().diff().dt.days.fillna(1)
    sig = (c > c.rolling(200).mean()) if filt else pd.Series(True, c.index)
    vol = r.rolling(20).std() * np.sqrt(252)
    w = (tv / vol).clip(upper=2.0) * sig                       # nominal / capital
    w = w.shift(1)                                             # se decide al cierre, rige al día siguiente
    pnl = w * r - w * fin - (w.diff().abs() * 0.0002)
    return pnl.dropna(), w
def portfolio(markup, filt=True, tv=0.10, start="1990"):
    P = pd.concat({n: market(n, markup, filt, tv)[0] for n in IDX}, axis=1)
    P = P[P.index >= start]
    return P.mean(axis=1, skipna=True)                          # equiponderado
def stats(s, a, b):
    q = s[(s.index >= a) & (s.index <= b)]
    ann = q.mean() * 252; vol = q.std() * np.sqrt(252); eq = (1 + q).cumprod(); dd = (eq / eq.cummax() - 1).min()
    yrs = q.groupby(q.index.year).sum()
    return f"ret {ann*100:+5.1f}%/año vol {vol*100:4.1f}% Sharpe {ann/vol:+.2f} t {ann/vol*np.sqrt(len(q)/252):+.2f} maxDD {dd*100:5.1f}% años+ {(yrs>0).mean():.0%}"
if __name__ == "__main__":
    for filt in (True, False):
        for mk in (0.025, 0.035):
            s = portfolio(mk, filt)
            print(f"{'filtro 200' if filt else 'sin filtro'} financ.+{mk*100:.1f}% | 1990-2007 {stats(s,'1990','2007-12-31')} | 2008-2026 {stats(s,'2008','2026-12-31')}")
    for n in IDX:
        s = market(n, 0.025)[0]; print(f"  {n:6s} 2008-2026 {stats(s,'2008','2026-12-31')}")
