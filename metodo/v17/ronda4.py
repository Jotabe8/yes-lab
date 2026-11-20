"""v17 ronda 4: (a) umbral de pruebas múltiples: Bonferroni por familia (n=10, lo que usa el embudo),
Bonferroni global, Holm, BH y BHY (Harvey-Liu recomiendan BHY) sobre TODA la cohorte; ¿cuántas pasan y qué
hacen fuera? (b) familias frente a variantes: ¿predice mejor la media de la familia o su mejor variante?"""
from pathlib import Path
from statistics import NormalDist
import numpy as np, pandas as pd

AQUI = Path(__file__).parent
N01 = NormalDist()
for arch in ("cohorte.csv.gz", "cohorte_2011.csv.gz"):
    d = pd.read_csv(AQUI / arch)
    print(f"\n######## {arch}")
    for y in ("tx", "t"):
        x = d.dropna(subset=[f"{y}_IS", f"{y}_OOS"]).copy()
        t, to = x[f"{y}_IS"].to_numpy(), x[f"{y}_OOS"].to_numpy()
        N = len(t)
        p = np.array([1 - N01.cdf(v) for v in t])
        orden = np.argsort(p)
        ps = p[orden]; k = np.arange(1, N + 1)
        def pasa_bh(c):
            ok = ps <= k * 0.05 / (N * c)
            m = np.zeros(N, bool)
            if ok.any():
                m[orden[: ok.nonzero()[0].max() + 1]] = True
            return m
        reglas = {
            "t ≥ 1,64 (sin corregir)": t >= 1.645,
            "Bonferroni n=10 (t ≥ 2,58)": t >= N01.inv_cdf(1 - 0.005),
            "Bonferroni n=100 (t ≥ 3,29)": t >= N01.inv_cdf(1 - 0.0005),
            "BH 5 % global": pasa_bh(1.0),
            "BHY 5 % global": pasa_bh(np.sum(1 / k)),
            f"Bonferroni global n={N}": t >= N01.inv_cdf(1 - 0.05 / N),
        }
        print(f"\nobjetivo {y}: {N} reglas")
        for nom, m in reglas.items():
            if m.sum() == 0:
                print(f"  {nom:<30} pasan    0"); continue
            print(f"  {nom:<30} pasan {m.sum():4d}  t_OOS medio {to[m].mean():+.2f}  % con t_OOS>1 {(to[m] > 1).mean():.0%}  "
                  f"% t_OOS>0 {(to[m] > 0).mean():.0%}  familias {x[m].familia.nunique()}")
        # (b) familias
        g = x.groupby(["clase", "familia", "lado"])
        f = pd.DataFrame({"media_is": g[f"{y}_IS"].mean(), "mejor_is": g[f"{y}_IS"].max(),
                          "media_oos": g[f"{y}_OOS"].mean(), "n": g.size()})
        # OOS de la mejor variante del ajuste
        idx = g[f"{y}_IS"].idxmax()
        f["mejor_oos"] = x.loc[idx.values, f"{y}_OOS"].values
        print(f"  familias×clase×lado: {len(f)}; Spearman(media_is, media_oos) {f.media_is.rank().corr(f.media_oos.rank()):+.2f}, "
              f"Spearman(mejor_is, media_oos) {f.mejor_is.rank().corr(f.media_oos.rank()):+.2f}")
        top = f.nlargest(10, "media_is"); topb = f.nlargest(10, "mejor_is")
        print(f"  top10 por media: media_oos {top.media_oos.mean():+.2f}, su mejor variante fuera {top.mejor_oos.mean():+.2f} | "
              f"top10 por mejor variante: media_oos {topb.media_oos.mean():+.2f}, mejor variante fuera {topb.mejor_oos.mean():+.2f}")
        print("  top 5 por media:", "; ".join(f"{a}/{b}/{c:+d} {r.media_is:+.2f}→{r.media_oos:+.2f}" for (a, b, c), r in top.head(5).iterrows()))
