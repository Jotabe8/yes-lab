# Prima nocturna tras un día de estrés: 3 índices de EE. UU. + 3 de Europa, y meseta del umbral.
import numpy as np, pandas as pd
from embudo import embudo, t_stat
STOP = 0.01
US = {"US500": ("ny_USA500IDXUSD.pkl", 9.5, 16.0, 9.58), "US30": ("ny_USA30IDXUSD.pkl", 9.5, 16.0, 9.58),
      "US2000": ("ny_USSC2000IDXUSD.pkl", 9.5, 16.0, 9.58)}
EU = {"FRA40": ("eu_FRA40.pkl", 9.0, 21.9, 9.1), "UK100": ("eu_UK100.pkl", 9.0, 21.9, 9.1),
      "EU50": ("eu_EU50.pkl", 9.0, 21.9, 9.1), "GER40": ("eu_GER40.pkl", 9.0, 21.75, 9.1)}

def cerca(d, h):
    t = pd.Timestamp(d.index[0].date()) + pd.Timedelta(hours=h)
    i = d.index.searchsorted(t)
    for j in (i, i - 1):
        if 0 <= j < len(d) and abs((d.index[j] - t).total_seconds()) <= 900: return d.iloc[j]
    return None

def ops(fich, h_ab, h_ci, h_sal, caida=None):
    v = pd.read_pickle(fich); v = v[~v.index.duplicated()].sort_index()
    dias = {f: d for f, d in v.groupby(v.index.date)}; fs = sorted(dias); filas = []
    for i, f in enumerate(fs[:-1]):
        if (fs[i + 1] - f).days > 4: continue
        d, dn = dias[f], dias[fs[i + 1]]
        ab, ci, sal = cerca(d, h_ab), cerca(d, h_ci), cerca(dn, h_sal)
        if ab is None or ci is None or sal is None: continue
        ret = ci.close / ab.open - 1
        e, st = ci.close, ci.close * STOP
        rb = (sal.open - e) / st  # sin tope: un hueco puede saltar el stop
        filas.append((pd.Timestamp(f), rb, (ci.spread + sal.spread) / 2 / st, ret))
    o = pd.DataFrame(filas, columns=["fecha", "r_bruto", "coste_r", "ret"])
    return o if caida is None else o[o.ret <= caida].reset_index(drop=True)

base = {n: ops(*v[:4]) for n, v in {**US, **EU}.items()}
for n, o in base.items(): print(n, len(o), "noches, bruto todas", round(o.r_bruto.mean(), 3))

for umbral in (-0.015,):
    tr = []
    for n, o in base.items():
        s = o[o.ret <= umbral]
        tr.append(s.assign(mercado=n))
    j = pd.concat(tr).sort_values("fecha").reset_index(drop=True)
    a = j.fecha < "2023"
    marca = " <== preregistrado" if umbral == -0.015 else ""
    print(f"\numbral {umbral:+.3f}: {len(j)} ops ({len(j)/8.8:.0f}/año) bruto {j.r_bruto.mean():+.3f} t {t_stat(j.r_bruto):.2f}"
          f" | IS {j[a].r_bruto.mean():+.3f} (n {a.sum()}) OOS {j[~a].r_bruto.mean():+.3f} (n {(~a).sum()}){marca}")
    if umbral == -0.015:
        print("  por mercado:", {n: (len(g), round(g.r_bruto.mean(), 3)) for n, g in j.groupby("mercado")})
        print("  por año (neto):", (j.r_bruto - j.coste_r).groupby(j.fecha.dt.year).mean().round(3).to_dict())
        todas = np.concatenate([o.r_bruto.to_numpy() for o in base.values()])
        print(f"  todas las noches: {todas.mean():+.3f} R (n {len(todas)})")
        plac = lambda s: np.random.default_rng(s).choice(todas, len(j))
        print(embudo(j[["fecha", "r_bruto", "coste_r"]], n_pruebas=12, corte_oos="2023-01-01", placebo=plac))
        j.to_csv("ops_noche_sin_tope.csv", index=False)
