"""PREREGISTRO_STOP_ANCHO.md: JP225 (horquilla FTMO 0,0157 %) y ETH (0,025 % + comisión 0,065 %), stop 0,15 / 0,30 ATR / extremo del rango."""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v3/"
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x))
def carga(sim):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(B + f"stop_ancho/ancho_{sim}_*.csv")))
    d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index(); return d[d.index.dayofweek < 5]
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
j = carga("JP225").dropna(subset=["r"]); e = carga("ETHUSD").dropna(subset=["r10"]); e = e[e.index >= "2021-03-01"]
d15 = 0.15 * e.atr
casos = {
    ("JP225", "0,15 ATR (base)"): (j.r, j.r_contra, j.dist, 0.000157, j.px),
    ("JP225", "V1 0,30 ATR"): (j.r_s30, j.c_s30, 2 * j.dist, 0.000157, j.px),
    ("JP225", "V2 extremo del rango"): (j.r_ext, j.c_ext, j.dist_ext, 0.000157, j.px),
    ("ETHUSD", "0,15 ATR (base)"): (e.r10, e.c10, d15, 0.00025 + 0.00065, e.px),
    ("ETHUSD", "V1 0,30 ATR"): (e.r10_s30, e.c10_s30, e.d10_s30, 0.00025 + 0.00065, e.px),
    ("ETHUSD", "V2 extremo del rango"): (e.r10_ext, e.c10_ext, e.d10_ext, 0.00025 + 0.00065, e.px),
}
filas = []
for (sim, v), (r, c, dist, k, px) in casos.items():
    cr = k * px / dist; n = r - cr; h = n.index[len(n) // 2]
    o = pd.concat([n, orb], axis=1, join="inner").dropna()
    filas.append(dict(mercado=sim, variante=v, ops=n.count(), coste_R=cr.mean(), bruto=r.mean(), neto=n.mean(), t=t(n),
                      mitad1=n[:h].mean(), mitad2=n[h:].mean(), x2=(r - 2 * cr).mean(), contra_neto=(c - cr).mean(),
                      exceso_t=t((r - c) / 2), corr_orb=o.iloc[:, 0].corr(o.iloc[:, 1]),
                      R_año=n.mean() * n.count() / (len(n.index.year.unique()) - 0.15)))
res = pd.DataFrame(filas); res.to_csv(B + "stop_ancho_resumen.csv", index=False)
pd.set_option("display.width", 250); print(res.round(3).to_string(index=False))
