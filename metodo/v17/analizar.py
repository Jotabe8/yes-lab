"""v17 ronda 1: ¿qué métrica de ajuste (2001-14) predice el fuera de muestra (2015-26)? Ver PREREGISTRO.md."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

AQUI = Path(__file__).parent
Y = sys.argv[1] if len(sys.argv) > 1 else "tx"        # tx = sin deriva (timing), t = bruto con exposición


def rasgos(d: pd.DataFrame, y: str) -> pd.DataFrame:
    d = d.copy()
    k = ["mercado", "familia", "lado"]
    d["t_is"] = d[f"{y}_IS"]
    # meseta: media de la regla y sus vecinos de rejilla (p1±1 o p2±1)
    idx = {tuple(r): v for r, v in zip(d[k + ["p1", "p2"]].itertuples(index=False), d.t_is)}
    def mesa(r):
        vs = [idx.get((r.mercado, r.familia, r.lado, r.p1 + a, r.p2 + b)) for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))]
        vs = [v for v in vs if v is not None and np.isfinite(v)]
        return np.mean(vs)
    d["meseta"] = [mesa(r) for r in d.itertuples(index=False)]
    # cruzado: misma regla en los demás mercados de la clase (sin el propio)
    g = d.groupby(["clase", "familia", "p1", "p2", "lado"]).t_is
    s, n = g.transform("sum"), g.transform("count")
    d["cruzado"] = ((s - d.t_is) / (n - 1)).where(n > 1)
    # estabilidad: peor de las dos mitades
    d["estab"] = np.minimum(d[f"{y}_A"], d[f"{y}_B"])
    # WFC: correlación A-B de la rejilla dentro de mercado×familia×lado
    def wfc(x):
        x = x.dropna(subset=[f"{y}_A", f"{y}_B"])
        return x[f"{y}_A"].rank().corr(x[f"{y}_B"].rank()) if len(x) >= 4 else np.nan
    w = d.groupby(k).apply(wfc, include_groups=False).rename("wfc")
    d = d.join(w, on=k)
    # EB jerárquico: encoge la t hacia la media de su familia×clase×lado según la varianza entre reglas
    gm = d.groupby(["clase", "familia", "lado"]).t_is
    m_f = gm.transform("mean")
    v_tot = d.t_is.var()
    tau2 = max(v_tot - 1.0, 0.0)        # varianza de la t verdadera (ruido ≈ 1 en unidades de t)
    b = tau2 / (tau2 + 1.0)
    d["eb_fam"] = m_f + b * (d.t_is - m_f)
    d["mesa_cruz"] = (d.meseta + d.cruzado.fillna(d.meseta)) / 2
    d["vol"] = d.vol_IS
    d["dd"] = -d.dd_IS
    return d, b


def boot_spearman(d, col, y, reps=500, seed=0):
    rng = np.random.default_rng(seed)
    ms = d.mercado.unique()
    base, alt = [], []
    for _ in range(reps):
        sel = rng.choice(ms, len(ms))
        x = pd.concat([d[d.mercado == m] for m in sel])
        base.append(x.t_is.rank().corr(x[y].rank()))
        alt.append(x[col].rank().corr(x[y].rank()))
    dif = np.array(alt) - np.array(base)
    return np.percentile(dif, [2.5, 97.5])


def main():
    d = pd.read_csv(AQUI / "cohorte.csv.gz").dropna(subset=[f"{Y}_IS", f"{Y}_OOS"])
    d, b = rasgos(d, Y)
    yo = f"{Y}_OOS"
    print(f"Cohorte {len(d)} reglas, objetivo {yo}; EB factor de encogimiento b = {b:.2f} "
          f"(std t_IS {d.t_is.std():.2f}; con ruido puro ≈ 1)")
    print(f"Pendiente MCO de {yo} sobre t_IS: {np.polyfit(d.t_is, d[yo], 1)[0]:.2f} (1 = sin encoger)")
    print("\nrasgo        Spearman  Δ vs t_IS [IC95 por mercados]   top5%: t_OOS medio  %t>0   top1%: t_OOS  %t>0")
    for col in ["t_is", "meseta", "cruzado", "mesa_cruz", "estab", "wfc", "eb_fam", "vol", "dd"]:
        x = d.dropna(subset=[col])
        rho = x[col].rank().corr(x[yo].rank())
        ic = boot_spearman(x, col, yo) if col != "t_is" else (0, 0)
        r = []
        for q in (0.05, 0.01):
            top = x[x[col] >= x[col].quantile(1 - q)]
            r += [top[yo].mean(), (top[yo] > 0).mean()]
        print(f"{col:<12} {rho:+.3f}   [{ic[0]:+.3f}, {ic[1]:+.3f}]            {r[0]:+.2f}  {r[1]:.0%}           {r[2]:+.2f}  {r[3]:.0%}")
    # controles
    print("\nControl positivo: IBS largo en índices US (p1=thr 0,2 o 0,1, todas las h)")
    c = d[(d.familia == "ibs") & (d.lado == 1) & d.mercado.isin(["GSPC", "NDX", "RUT", "DJI", "ES", "NQ", "YM"])]
    for col in ["t_is", "meseta", "cruzado", "estab", "eb_fam"]:
        pct = (d[col].rank(pct=True)).loc[c.index]
        print(f"  {col:<10} percentil medio {pct.mean():.0%}, mínimo {pct.min():.0%}")
    print(f"  {yo} medio {c[yo].mean():+.2f}")
    print("\nPor familia (media t_is vs media OOS, solo lado +1 y −1):")
    print(d.groupby(["familia", "lado"])[["t_is", yo]].mean().round(2).unstack().to_string())


if __name__ == "__main__":
    main()
