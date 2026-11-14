"""Candidato 3 v4 (PREREGISTRO_V4_R2.md): corto financiación alta / largo financiación baja, semanal, perpetuos."""
import glob, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))
def velas(f):
    k = pd.read_csv(f); k = k[pd.to_numeric(k.open_time, errors="coerce").notna()]
    ot = k.open_time.astype("int64"); ot = np.where(ot > 1e14, ot // 1000, ot)
    return pd.Series(k.close.astype(float).to_numpy(), index=pd.to_datetime(ot, unit="ms").normalize()).groupby(level=0).last()
P, F = {}, {}
for f in glob.glob(D + "bn_*_funding.csv.gz"):
    m = os.path.basename(f).split("_")[1]
    fr = pd.read_csv(f); fr = fr[pd.to_numeric(fr.calc_time, errors="coerce").notna()]
    s = pd.Series(fr.last_funding_rate.astype(float).to_numpy(), index=pd.to_datetime(fr.calc_time.astype("int64"), unit="ms"))
    F[m] = s.groupby(s.index.floor("D")).sum()
    P[m] = velas(D + f"bn_{m}_perp1d.csv.gz")
P = pd.DataFrame(P).sort_index(); F = pd.DataFrame(F).reindex(P.index)
# vela diaria fechada en d = apertura d 00:00 → cierre d 23:59; rentabilidad del día d = close_d / close_{d-1} - 1
rp = P.pct_change()
elig = P.notna().rolling(60).sum() >= 60
señal = F.rolling(7, min_periods=7).mean().shift(1)       # media de los 7 días previos a d (conocida a las 00:00 de d)
lunes = P.index[P.index.dayofweek == 0]
def pesos(q=1/3, aleatorio=None):
    W = pd.DataFrame(np.nan, index=P.index, columns=P.columns)
    for d in lunes:
        s = señal.loc[d][elig.loc[d] & señal.loc[d].notna()]
        if len(s) < 6: W.loc[d] = 0; continue
        if aleatorio is not None: s = pd.Series(aleatorio.permutation(s.values), s.index)
        k = max(1, int(len(s) * q)); o = s.sort_values()
        w = pd.Series(0.0, P.columns); w[o.index[:k]] = 0.5 / k; w[o.index[-k:]] = -0.5 / k
        W.loc[d] = w
    return W.ffill().fillna(0)
def correr(W, con_fin=True, mult=1.0):
    bruto = (W * rp.fillna(0)).sum(1) - (W * F.fillna(0)).sum(1) * con_fin   # corto cobra financiación positiva
    rot = W.diff().abs().sum(1)
    return (bruto - mult * rot * 0.0007)[P.index >= "2020-03-01"]
W1 = pesos()
r1, r2v, rx2 = correr(W1), correr(W1, con_fin=False), correr(W1, mult=2)
r3 = correr(pesos(0.2))
mitad = r1.index[len(r1) // 2]
for nom, r in (("V1 tercios, precio+financiación", r1), ("V2 solo precio", r2v), ("V3 quintiles", r3), ("V1 costes ×2", rx2)):
    print(f"{nom:32s} anual {r.mean()*365:+.1%} vol {r.std()*np.sqrt(365):.1%} Sharpe {r.mean()/r.std()*np.sqrt(365):.2f} t {t(r):.2f} | 1ª {r[:mitad].mean()*365:+.1%} 2ª {r[mitad:].mean()*365:+.1%}")
print("por año V1 %:", (r1.groupby(r1.index.year).mean() * 365 * 100).round(1).to_dict())
rng = np.random.default_rng(0)
pl = [correr(pesos(aleatorio=rng)).mean() for _ in range(300)]
print(f"placebo ordenación aleatoria p95 {np.percentile(pl,95)*365:+.1%} (media {np.mean(pl)*365:+.1%}) vs V1 {r1.mean()*365:+.1%}")
r1.rename("r").to_frame().to_csv("metodo/v4/funding_transversal_diaria.csv")
