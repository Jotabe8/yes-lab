# La noche como UNA operación: se reparte el riesgo entre los mercados que disparan esa noche.
import numpy as np, pandas as pd
from embudo import embudo, t_stat, ftmo_2step, montecarlo_dd
o = pd.read_csv("ops_noche_6mercados.csv", parse_dates=["fecha"])
o["neto"] = o.r_bruto - o.coste_r
g = o.groupby("fecha")
noches = pd.DataFrame({"fecha": g.size().index, "n": g.size().values,
                       "r_bruto": g.r_bruto.mean().values, "coste_r": g.coste_r.mean().values})
print(f"noches: {len(noches)} ({len(noches)/8.8:.0f}/año), mercados por noche {noches.n.mean():.1f}")
print(f"R por noche (riesgo 1R repartido): bruto {noches.r_bruto.mean():+.3f} t {t_stat(noches.r_bruto):.2f}"
      f" | IS {noches[noches.fecha<'2023'].r_bruto.mean():+.3f} | OOS {noches[noches.fecha>='2023'].r_bruto.mean():+.3f}")
todas = np.load("todas_noches.npy") if False else None
plac = lambda s: np.random.default_rng(s).normal(0, noches.r_bruto.std(), len(noches)) + 0.059
print(embudo(noches, n_pruebas=12, corte_oos="2023-01-01"))

# correlación diaria con el ORB US100
orb = pd.read_csv("orb_v018.csv", parse_dates=["d"]).rename(columns={"d": "fecha", "Rbe": "r_orb"})[["fecha", "r_orb"]]
j = pd.merge(noches[["fecha"]].assign(r=(noches.r_bruto - noches.coste_r).values), orb, on="fecha", how="outer").fillna(0)
print(f"\ncorrelación diaria con el ORB US100: {j.r.corr(j.r_orb):.3f} (n días {len(j)}, solapados {((j.r!=0)&(j.r_orb!=0)).sum()})")
d = (noches.r_bruto - noches.coste_r)
print("DD máx Monte Carlo (R):", montecarlo_dd(d.to_numpy()))
print("peor noche:", d.min(), "| peor mes:", d.groupby(noches.fecha.dt.to_period('M')).sum().min())
