"""Candidato 9 v4 (PREREGISTRO_V4_R7.md): apostar contra la beta con ETF sectoriales (V1) y de país (réplica)."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
def px(s):
    d = pd.read_csv(D + f"bab_{s}.csv"); i = pd.to_datetime(d.iloc[:, 0], errors="coerce"); d = d[i.notna()]; i = i[i.notna()]
    col = "Adj Close" if "Adj Close" in d and pd.to_numeric(d["Adj Close"], errors="coerce").notna().any() else "Close"
    return pd.Series(pd.to_numeric(d[col], errors="coerce").to_numpy(), i.values).dropna()
irx = px("IRX"); 
def bab(univ, mkt=None, k=3, escalar=True, c=0.0002, borrow=0.0025, azar=None):
    P = pd.DataFrame({s: px(s) for s in univ}).sort_index()
    R = P.pct_change(fill_method=None)
    M = px(mkt).reindex(P.index).pct_change(fill_method=None) if mkt else R.mean(axis=1)
    rf = (irx.reindex(R.index).ffill() / 100 / 252).fillna(0)
    fin = R.index.to_series().groupby(R.index.to_period("M")).max().values   # último día de cada mes
    w = pd.DataFrame(0.0, R.index, univ); bL = bH = None; cur = pd.Series(0.0, index=univ)
    filas = []
    for d in fin:
        j = R.index.get_loc(d)
        if j < 260: continue
        x = R.iloc[j - 252:j]; m = M.iloc[j - 252:j]          # hasta el día anterior
        ok = [s for s in univ if x[s].notna().sum() > 240]
        if len(ok) < 2 * k: continue
        beta = {s: np.cov(x[s].fillna(0), m.fillna(0))[0, 1] / m.fillna(0).var() for s in ok}
        beta = pd.Series(beta) * 0.6 + 0.4
        orden = beta.sort_values().index.tolist()
        if azar is not None: orden = list(azar.permutation(orden))
        L, H = orden[:k], orden[-k:]
        bl, bh = beta[L].mean(), beta[H].mean()
        nuevo = pd.Series(0.0, index=univ)
        nuevo[L] = (1 / bl if escalar else 1) / k; nuevo[H] = -(1 / bh if escalar else 1) / k
        filas.append((d, nuevo, cur)); cur = nuevo
    pos = pd.DataFrame({d: n for d, n, _ in filas}).T.reindex(R.index).ffill().shift(1).fillna(0)  # posición fijada al cierre d, rinde desde d+1
    giro = pd.Series({d: (n - o).abs().sum() for d, n, o in filas}).reindex(R.index).fillna(0)
    exc = R.sub(rf, axis=0).fillna(0)
    r = (pos * exc).sum(axis=1) - giro * c - pos.clip(upper=0).abs().sum(axis=1) * borrow / 252
    primero = pos.abs().sum(axis=1).ne(0).idxmax()
    return r.loc[primero:]
def informe(nombre, r):
    m = r.index[len(r) // 2]; vol = r.std() * np.sqrt(252); e = r * 0.15 / vol; eq = e.cumsum(); dd = (eq - eq.cummax()).min()
    print(f"{nombre} {r.index[0].date()}→{r.index[-1].date()}: {r.mean()*252:+.2%}/año t {t(r):.2f} | 1ª {r[:m].mean()*252:+.2%} 2ª {r[m:].mean()*252:+.2%} | "
          f"vol {vol:.1%}; a 15 %: {e.mean()*252:+.1%}/año, DD {dd:.1%} ({abs(dd)/max(e.mean()*252,1e-9):.1f}× beneficio anual)")
SEC = "XLB XLE XLF XLI XLK XLP XLU XLV XLY".split()
r1 = bab(SEC, "SPY"); informe("V1 sectores", r1)
print("   por año %:", (r1.groupby(r1.index.year).sum() * 100).round(1).to_dict())
r2 = bab(SEC, "SPY", c=0.0004, borrow=0.005); informe("V1 costes ×2", r2)
rng = np.random.default_rng(11); pl = [bab(SEC, "SPY", azar=rng).mean() for _ in range(200)]
print(f"placebo (3/3 al azar cada mes): p95 {np.percentile(pl,95)*252:+.2%}/año (media {np.mean(pl)*252:+.2%}) vs V1 {r1.mean()*252:+.2%}")
PAIS = "EWA EWC EWD EWG EWH EWI EWJ EWK EWL EWM EWN EWO EWP EWQ EWS EWU EWW EWY EWT EWZ".split()
rp = bab(PAIS, None, k=4); informe("Réplica países", rp)
r3 = bab(SEC, "SPY", escalar=False); informe("V3 sectores sin escalar", r3)
r1.rename("r").to_frame().to_csv("metodo/v4/bab_v1_diaria.csv")
