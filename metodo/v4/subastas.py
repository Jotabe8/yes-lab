"""Candidato 8 v4 (PREREGISTRO_V4_R6.md): ciclo de subastas del Tesoro en IEF."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
sub = pd.read_csv(D + "subastas.csv")
sub["auction_date"] = pd.to_datetime(sub.auction_date, errors="coerce")
nom = sub[sub.security_type.isin(["Note", "Bond"])]
for c in ("inflation_index_security", "floating_rate"):
    if c in nom: nom = nom[nom[c].astype(str).str.lower().isin(["no", "n", "false", "nan", "null"])]
nom = nom[(nom.auction_date >= "2002-06-01")]
plazo = nom.security_term.astype(str).str.extract(r"(\d+)-Year")[0].astype(float)
print("subastas:", len(nom), "por plazo:", plazo.value_counts().sort_index().to_dict())
def precio(s):
    d = pd.read_csv(D + f"{s}.csv"); d = d[pd.to_datetime(d.iloc[:, 0], errors="coerce").notna()]
    col = "Adj Close" if "Adj Close" in d and d["Adj Close"].notna().any() else "Close"
    return pd.Series(pd.to_numeric(d[col], errors="coerce").to_numpy(), pd.to_datetime(d.iloc[:, 0])).dropna()
def senal(idx, fechas, pre=True, post=True):
    pos = np.searchsorted(idx.values, np.array(sorted(set(fechas)), dtype="datetime64[ns]"))
    s = np.zeros(len(idx))
    for p in pos:
        if p >= len(idx): continue
        if pre: s[max(0, p - 4):p + 1] -= 1
        if post: s[p + 1:p + 5] += 1
    return pd.Series(np.sign(s), idx)
def correr(nombre, s, fechas, c=0.0001, **kw):
    p = precio(s); r = p.pct_change().dropna(); p = p.loc[r.index]
    pos = senal(r.index, fechas, **kw)
    neto = pos * r - pos.diff().abs().fillna(abs(pos.iloc[0])) * c
    return pos, r, neto
f_all = nom.auction_date
pos, r, n1 = correr("IEF", "IEF", f_all)
m = n1.index[len(n1) // 2]
print(f"V1 IEF {n1.index[0].date()}→{n1.index[-1].date()}: {n1.mean()*252:+.2%}/año t {t(n1):.2f} | 1ª {n1[:m].mean()*252:+.2%} 2ª {n1[m:].mean()*252:+.2%} | días con posición {(pos!=0).mean():.0%}")
print("   por año:", (n1.groupby(n1.index.year).sum() * 100).round(2).to_dict())
_, _, n2 = correr("IEF", "IEF", f_all, c=0.0002); print(f"V1 costes ×2: {n2.mean()*252:+.2%}/año t {t(n2):.2f}")
rng = np.random.default_rng(5); pl = []
for i in range(200):
    k = int(rng.integers(20, len(pos) - 20)); ps = pd.Series(np.roll(pos.values, k), pos.index)
    pl.append((ps * r - ps.diff().abs().fillna(0) * 0.0001).mean())
print(f"placebo rotación: p95 {np.percentile(pl,95)*252:+.2%}/año (media {np.mean(pl)*252:+.2%}) vs V1 {n1.mean()*252:+.2%}")
_, _, v2 = correr("IEF", "IEF", nom.auction_date[plazo.isin([10, 30]).values]); print(f"V2 solo 10 y 30 años: {v2.mean()*252:+.2%}/año t {t(v2):.2f}")
_, _, a = correr("IEF", "IEF", f_all, post=False); _, _, b = correr("IEF", "IEF", f_all, pre=False)
print(f"V3 solo pata previa (corto): {a.mean()*252:+.2%}/año t {t(a):.2f} | solo posterior (largo): {b.mean()*252:+.2%}/año t {t(b):.2f}")
print("Réplicas (informativas hasta que pase V1):")
for s in ("TLT", "ZN_F", "ZB_F", "ZF_F", "IEI"):
    try:
        _, _, x = correr(s, s, f_all); y = x[x.index >= "2009-01-01"]
        print(f"   {s}: {x.mean()*252:+.2%}/año t {t(x):.2f} | 2009+ {y.mean()*252:+.2%} t {t(y):.2f}")
    except Exception as e: print("  ", s, e)
y = n1[n1.index >= "2009-01-01"]; print(f"   IEF 2009+: {y.mean()*252:+.2%}/año t {t(y):.2f}")
n1.rename("r").to_frame().to_csv("metodo/v4/subastas_v1_diaria.csv")
