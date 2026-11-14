"""Candidato 5 v4 (PREREGISTRO_V4_R3.md): reversión semanal transversal en 20 perpetuos."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, runpy
g = runpy.run_path("metodo/v4/funding_transversal.py.base", run_name="x") if False else None
exec(open("metodo/v4/funding_transversal.py").read().split("W1 = pesos()")[0])   # carga P, F, rp, elig, correr
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
def pesos_rev(dias_ret=7, frec="W", aleatorio=None, q=1/3):
    ret = P.pct_change(dias_ret).shift(1)                 # rentabilidad hasta el cierre de d-1 (conocida a las 00:00 de d)
    W = pd.DataFrame(np.nan, index=P.index, columns=P.columns)
    fechas = P.index[P.index.dayofweek == 0] if frec == "W" else P.index
    for d in fechas:
        s = ret.loc[d][elig.loc[d] & ret.loc[d].notna()]
        if len(s) < 6: W.loc[d] = 0; continue
        if aleatorio is not None: s = pd.Series(aleatorio.permutation(s.values), s.index)
        k = max(1, int(len(s) * q)); o = s.sort_values()
        w = pd.Series(0.0, P.columns); w[o.index[:k]] = 0.5 / k; w[o.index[-k:]] = -0.5 / k   # largo perdedores
        W.loc[d] = w
    return W.ffill().fillna(0)
W = pesos_rev()
r1, rx2, r3 = correr(W), correr(W, mult=2), correr(W, con_fin=False)
r2 = correr(pesos_rev(1, "D"))
mitad = r1.index[len(r1) // 2]
for nom, r in (("V1 semanal", r1), ("V2 diaria", r2), ("V3 sin financiación", r3), ("V1 costes ×2", rx2)):
    print(f"{nom:22s} anual {r.mean()*365:+.1%} vol {r.std()*np.sqrt(365):.1%} t {t(r):.2f} | 1ª {r[:mitad].mean()*365:+.1%} 2ª {r[mitad:].mean()*365:+.1%}")
print("por año V1 %:", (r1.groupby(r1.index.year).mean() * 365 * 100).round(1).to_dict())
rng = np.random.default_rng(1); pl = [correr(pesos_rev(aleatorio=rng)).mean() for _ in range(300)]
print(f"placebo p95 {np.percentile(pl,95)*365:+.1%} vs V1 {r1.mean()*365:+.1%}")
