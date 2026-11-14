"""Candidato 10 v4 (PREREGISTRO_V4_R8.md): cambio de año en pequeñas compañías."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
def px(s):
    d = pd.read_csv(D + f"ene_{s}.csv"); i = pd.to_datetime(d.iloc[:, 0], errors="coerce"); d = d[i.notna()]; i = i[i.notna()]
    col = "Adj Close" if "Adj Close" in d and pd.to_numeric(d["Adj Close"], errors="coerce").notna().any() else "Close"
    return pd.Series(pd.to_numeric(d[col], errors="coerce").to_numpy(), i.values).dropna()
def ventanas(idx, mes=None, rng=None):
    """Devuelve lista de (inicio, fin) por invierno: cierre 5º día antes del último de dic → cierre 5º día hábil de ene."""
    out = []
    for y in sorted(set(idx.year)):
        dic = idx[(idx.year == y) & (idx.month == 12)]; ene = idx[(idx.year == y + 1) & (idx.month == 1)]
        if len(dic) < 8 or len(ene) < 6: continue
        a, b = dic[-6], ene[4]
        if rng is not None:                    # placebo: misma longitud en otro mes al azar de ese año
            n = idx.get_loc(b) - idx.get_loc(a); m = int(rng.integers(2, 12))
            mm = idx[(idx.year == y) & (idx.month == m)]
            if len(mm) < 6: continue
            j = idx.get_loc(mm[int(rng.integers(0, len(mm)))]); 
            if j + n >= len(idx): continue
            a, b = idx[j], idx[j + n]
        out.append((a, b))
    return out
def serie(peq, gran, a0, a1, c=0.0002, vent=None, rng=None, parte=None):
    p, g = px(peq), px(gran); idx = p.index.intersection(g.index); p, g = p[idx], g[idx]
    idx = idx[(idx.year >= a0) & (idx.year <= a1 + 1)]
    ls = (p.pct_change() - g.pct_change()).reindex(idx)
    r = pd.Series(0.0, idx); dentro = pd.Series(False, idx)
    for a, b in ventanas(idx, rng=rng):
        if a.year < a0 or a.year > a1: continue
        sel = (idx > a) & (idx <= b)
        if parte == "dic": sel &= (idx.year == a.year)
        if parte == "ene": sel &= (idx.year == a.year + 1)
        r[sel] = ls[sel]; dentro |= sel
        d = idx[sel]
        if len(d): r[d[0]] -= 2 * c; r[d[-1]] -= 2 * c
    return r[dentro], dentro
def informe(n, r):
    años = r.groupby(r.index.year - (r.index.month == 1)).sum()
    m = len(años) // 2
    print(f"{n}: inviernos {len(años)}, días {len(r)}, media por invierno {años.mean():+.2%} t(días) {t(r):.2f} | "
          f"1ª mitad {años.iloc[:m].mean():+.2%} 2ª {años.iloc[m:].mean():+.2%} | % inviernos + {(años>0).mean():.0%}")
    return años
r1, _ = serie("IWM", "SPY", 2000, 2025); a1 = informe("V1 IWM−SPY 2000-2025", r1)
print("   por invierno %:", (a1 * 100).round(2).to_dict())
vol = r1.std() * np.sqrt(252); e = a1 * 0.15 / vol; eq = e.cumsum(); dd = (eq - eq.cummax()).min()
print(f"   a vol 15 % (en días de ventana): {e.mean():+.1%}/año, DD {dd:.1%} ({abs(dd)/max(e.mean(),1e-9):.1f}× beneficio anual)")
r2, _ = serie("IWM", "SPY", 2000, 2025, c=0.0004); informe("V1 costes ×2", r2)
rng = np.random.default_rng(13); pl = []
for i in range(200):
    rp, _ = serie("IWM", "SPY", 2000, 2025, rng=rng); pl.append(rp.groupby(rp.index.year).sum().mean())
print(f"placebo (otro mes al azar): p95 {np.percentile(pl,95):+.2%} por año (media {np.mean(pl):+.2%}) vs V1 {a1.mean():+.2%}")
rr, _ = serie("RUT", "GSPC", 1988, 1999); informe("Réplica ^RUT−^GSPC 1988-1999", rr)
rv, _ = serie("RUT", "GSPC", 2000, 2025); informe("   (^RUT−^GSPC 2000-2025, control)", rv)
informe("V2 solo diciembre", serie("IWM", "SPY", 2000, 2025, parte="dic")[0])
informe("V3 solo enero", serie("IWM", "SPY", 2000, 2025, parte="ene")[0])
