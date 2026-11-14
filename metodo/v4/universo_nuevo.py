"""Ronda 4 (PREREGISTRO_V4_R4.md): momentum transversal y réplica del carry en el universo cripto NO visto."""
import glob, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
def velas(f):
    k = pd.read_csv(f); k = k[pd.to_numeric(k.open_time, errors="coerce").notna()]
    ot = k.open_time.astype("int64"); ot = np.where(ot > 1e14, ot // 1000, ot); i = pd.to_datetime(ot, unit="ms").normalize()
    return (pd.Series(k.close.astype(float).to_numpy(), i).groupby(level=0).last(),
            pd.Series(k.iloc[:, 7].astype(float).to_numpy(), i).groupby(level=0).last())
P, V, S, F = {}, {}, {}, {}
for f in glob.glob(D + "*_perp1d.csv.gz"):
    m = os.path.basename(f).split("_")[0]
    if os.path.basename(f).startswith("bn_"): continue
    P[m], V[m] = velas(f)
    if os.path.exists(D + f"{m}_spot1d.csv.gz"): S[m] = velas(D + f"{m}_spot1d.csv.gz")[0]
    if os.path.exists(D + f"{m}_funding.csv.gz"):
        fr = pd.read_csv(D + f"{m}_funding.csv.gz"); fr = fr[pd.to_numeric(fr.calc_time, errors="coerce").notna()]
        s = pd.Series(fr.last_funding_rate.astype(float).to_numpy(), pd.to_datetime(fr.calc_time.astype("int64"), unit="ms"))
        F[m] = s.groupby(s.index.floor("D")).sum()
P = pd.DataFrame(P).sort_index(); P = P[P.index >= "2019-09-01"]
V = pd.DataFrame(V).reindex(P.index); F = pd.DataFrame(F).reindex(index=P.index, columns=P.columns)
S = pd.DataFrame(S).reindex(P.index)
print("monedas nuevas:", P.shape[1], "con contado:", S.shape[1])
rp = P.pct_change()
rp = rp.where(rp.abs() < 3)   # rentabilidades diarias > 300 % = error de datos o deslistado; fuera
vol30 = V.rolling(30, min_periods=20).mean().shift(1)
elig = (P.notna().rolling(60).sum() >= 60) & (vol30.rank(axis=1, pct=True) >= 2 / 3)
print("elegibles medios por día:", round(elig.sum(1)[elig.index >= "2020-03-01"].mean(), 1))
def pesos(senal, aleatorio=None, q=1/3):
    W = pd.DataFrame(np.nan, index=P.index, columns=P.columns)
    for d in P.index[P.index.dayofweek == 0]:
        s = senal.loc[d][elig.loc[d] & senal.loc[d].notna()]
        if len(s) < 6: W.loc[d] = 0; continue
        if aleatorio is not None: s = pd.Series(aleatorio.permutation(s.values), s.index)
        k = max(1, int(len(s) * q)); o = s.sort_values()
        w = pd.Series(0.0, P.columns); w[o.index[-k:]] = 0.5 / k; w[o.index[:k]] = -0.5 / k   # largo ganadores
        W.loc[d] = w
    return W.ffill().fillna(0)
def correr(W, con_fin=True, mult=1.0):
    bruto = (W * rp.fillna(0)).sum(1) - (W * F.fillna(0)).sum(1) * con_fin
    return (bruto - mult * W.diff().abs().sum(1) * 0.0007)[P.index >= "2020-03-01"]
mom28, mom7 = P.pct_change(28).shift(1), P.pct_change(7).shift(1)
W = pesos(mom28)
r1, r2, r3, rx2 = correr(W), correr(pesos(mom7)), correr(W, con_fin=False), correr(W, mult=2)
mitad = r1.index[len(r1) // 2]
print("== Candidato 6: momentum transversal semanal (universo nuevo)")
for nom, r in (("V1 28 días", r1), ("V2 7 días", r2), ("V3 sin financiación", r3), ("V1 costes ×2", rx2)):
    print(f"{nom:22s} anual {r.mean()*365:+.1%} vol {r.std()*np.sqrt(365):.1%} Sharpe {r.mean()/r.std()*np.sqrt(365):.2f} t {t(r):.2f} | 1ª {r[:mitad].mean()*365:+.1%} 2ª {r[mitad:].mean()*365:+.1%}")
print("por año V1 %:", (r1.groupby(r1.index.year).mean() * 365 * 100).round(1).to_dict())
rng = np.random.default_rng(2); pl = [correr(pesos(mom28, aleatorio=rng)).mean() for _ in range(300)]
print(f"placebo p95 {np.percentile(pl,95)*365:+.1%} vs V1 {r1.mean()*365:+.1%}")
eq = r1.cumsum(); print(f"DD máx (suma simple) {(eq.cummax()-eq).max():.0%}; peor semana {r1.resample('W').sum().min():.1%}")
r1.rename("r").to_frame().to_csv("metodo/v4/momentum_nuevo_diaria.csv")

print("== Réplica carry (regla V1 del candidato 2) en universo nuevo")
cols = [c for c in S.columns if c in F.columns]
Rc = (S[cols].pct_change() - P[cols].pct_change()) + F[cols]
Rc = Rc.where(Rc.abs() < 0.5)
m7 = (F[cols] / 3).rolling(7, min_periods=7).mean().shift(2)
okc = (S[cols].notna() & P[cols].notna()).rolling(60).sum() >= 60
E = pd.DataFrame(0.0, index=Rc.index, columns=cols)
for c in cols:
    on = False; out = np.zeros(len(E))
    for i, (v, ok) in enumerate(zip(m7[c].to_numpy(), okc[c].to_numpy())):
        if np.isnan(v) or not ok: on = False
        elif not on and v > 0.0001: on = True
        elif on and v < 0: on = False
        out[i] = on
    E[c] = out
n = E.sum(1); neto = (E * Rc.fillna(0) - E.diff().abs().fillna(E) * 0.0015).sum(1) / n.replace(0, np.nan)
rc = neto.fillna(0)[Rc.index >= "2020-03-01"]
tb = {2020: 0.4, 2021: 0.05, 2022: 2.0, 2023: 5.1, 2024: 5.0, 2025: 4.2, 2026: 3.8}
rf = pd.Series({pd.Timestamp(f"{y}-01-01"): v / 100 for y, v in tb.items()}).reindex(rc.index, method="ffill") / 365
exc = (rc - rf) * (n[rc.index] > 0)
print(f"carry nuevo: monedas {len(cols)}, anual {rc.mean()*365:+.1%} t {t(rc):.2f}; exceso sobre letras {exc.mean()*365:+.2%} t {t(exc):.2f}")
print("  exceso por año %:", (exc.groupby(exc.index.year).mean() * 365 * 100).round(2).to_dict())
u = exc[exc.index >= exc.index[-1] - pd.Timedelta(days=365)]; print(f"  exceso últimos 12 meses {u.mean()*365:+.2%}; días con posición {(n[u.index]>0).mean():.0%}")
