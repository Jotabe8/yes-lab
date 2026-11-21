"""v17 ronda 3: ¿el t con ruido en el OHLC (noise test) predice el fuera mejor que el t limpio?"""
from pathlib import Path
import numpy as np, pandas as pd
from metodo.v17.analizar import boot_spearman

AQUI = Path(__file__).parent
d = pd.read_csv(AQUI / "cohorte.csv.gz")
r = pd.read_csv(AQUI / "ruido.csv.gz")
d = d.merge(r, on=["mercado", "familia", "p1", "p2", "lado"])
for y in ("tx", "t"):
    x = d.dropna(subset=[f"{y}_IS", f"{y}_OOS"]).copy()
    x["t_is"] = x[f"{y}_IS"]
    x["ruido"] = x[f"{y}_ruido"]
    x["caida"] = x.ruido - x.t_is                # cuánto pierde con ruido (más negativo = frágil)
    x["min_lr"] = np.minimum(x.t_is, x.ruido)
    yo = f"{y}_OOS"
    print(f"\nobjetivo {yo}: n {len(x)}, corr(t_is, ruido) {x.t_is.corr(x.ruido):.2f}")
    for col in ("t_is", "ruido", "min_lr", "caida"):
        rho = x[col].rank().corr(x[yo].rank())
        ic = boot_spearman(x, col, yo) if col != "t_is" else (0, 0)
        top = x[x[col] >= x[col].quantile(0.95)]
        print(f"  {col:<7} Spearman {rho:+.3f}  Δ IC95 [{ic[0]:+.3f}, {ic[1]:+.3f}]  top5% t_OOS {top[yo].mean():+.2f} ({(top[yo] > 0).mean():.0%} > 0)")
    c = x[(x.familia == "ibs") & (x.lado == 1) & x.mercado.isin(["GSPC", "NDX", "RUT", "DJI", "ES", "NQ", "YM"])]
    print(f"  control IBS US: t_is {c.t_is.mean():.2f} → con ruido {c.ruido.mean():.2f}; resto de la cohorte {x.t_is.mean():.2f} → {x.ruido.mean():.2f}")
