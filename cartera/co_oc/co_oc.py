import numpy as np, pandas as pd
from embudo import embudo, t_stat
def serie(f): v = pd.read_pickle(f); return v[~v.index.duplicated()].sort_index()
G = {"EEUU": ({"US500": "../shock0830/ny_USA500IDXUSD.pkl", "US30": "../shock0830/ny_USA30IDXUSD.pkl",
               "US2000": "../shock0830/ny_USSC2000IDXUSD.pkl"}, "09:30", "15:59"),
     "Europa": ({"FRA40": "../shock0830/eu_FRA40.pkl", "EU50": "../shock0830/eu_EU50.pkl",
                 "UK100": "../shock0830/eu_UK100.pkl"}, "09:01", "21:54")}
for g, (mk, ab, ci) in G.items():
    filas = {}
    for m, f in mk.items():
        v = serie(f); d = {}
        for dia, x in v.groupby(v.index.date):
            a = x.between_time(ab, ab); c = x.between_time(ci, ci)
            if len(a) and len(c): d[pd.Timestamp(dia)] = (a.open.iloc[0], a.spread.iloc[0], c.close.iloc[0], c.spread.iloc[0])
        filas[m] = pd.DataFrame(d, index=["o", "so", "c", "sc"]).T
    idx = sorted(set.intersection(*[set(x.index) for x in filas.values()]))
    P = {m: x.loc[idx] for m, x in filas.items()}
    noche = pd.DataFrame({m: P[m].o / P[m].c.shift(1) - 1 for m in P})
    dia = pd.DataFrame({m: P[m].c / P[m].o - 1 for m in P})
    coste = pd.DataFrame({m: (P[m].so + P[m].sc) / 2 / P[m].o for m in P})   # una vuelta por pata ≈ spread medio
    ok = noche.notna().all(axis=1) & (pd.Series(idx, index=idx).diff().dt.days <= 4)
    noche, dia, coste = noche[ok], dia[ok], coste[ok]
    lo, hi = noche.idxmin(axis=1), noche.idxmax(axis=1)
    bruto = np.array([dia.at[t, lo[t]] - dia.at[t, hi[t]] for t in dia.index]) / 2   # 50 % del nocional en cada pata
    cst = np.array([coste.at[t, lo[t]] + coste.at[t, hi[t]] for t in dia.index]) / 2
    fechas = pd.Series(dia.index)
    R = np.std(bruto[fechas < "2023"], ddof=1)
    ops = pd.DataFrame({"fecha": fechas, "r_bruto": bruto / R, "coste_r": cst / R})
    a = ops.fecha < "2023"
    print(f"\n=== {g}: {len(ops)} días, 1R = {R*100:.3f} % | bruto {bruto.mean()*100:+.4f} %/día t {t_stat(bruto):.2f} | coste {cst.mean()*100:.4f} %"
          f" | ajuste {ops[a].r_bruto.mean():+.3f} R, OOS {ops[~a].r_bruto.mean():+.3f} R")
    def plac(s):
        r = np.random.default_rng(s); out = []
        for t in dia.index:
            x, y = r.choice(dia.columns, 2, replace=False); out.append((dia.at[t, x] - dia.at[t, y]) / 2 / R)
        return np.array(out)
    print(embudo(ops, n_pruebas=2, corte_oos="2023-01-01", placebo=plac, n_placebo=100))
    ops.to_csv(f"ops_{g}.csv", index=False)
