import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v3/"
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
SPR = {"US100": 0.000049, "US500": 0.00008, "US30": 0.00005, "GER40": 0.000052}
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
d = pd.concat(pd.read_csv(f) for f in glob.glob(B + "choques/choques_*.csv")); d["fecha"] = pd.to_datetime(d.fecha); d = d.reset_index(drop=True)
d["c"] = d.sim.map(SPR) * d.px / d.dist
print("eventos por mercado y año (k>=4):"); print(d[d.z >= 4].groupby([d.sim, d.fecha.dt.year]).size().unstack(0).to_string())
print("coste medio R:", d.groupby("sim").c.mean().round(3).to_dict(), "| choque medio % precio:", (d.dist / d.px * 100).groupby(d.sim).mean().round(3).to_dict())
filas = []
for k in (4, 3):
    e = d[d.z >= k]
    for nom, col in (("contra 30", "r30"), ("contra 60", "r60"), ("seguir 30 (placebo 1)", "seguir30"), ("día anterior (placebo 2)", "placebo30")):
        for sim, g in list(e.groupby("sim")) + [("TODOS", e)]:
            x = (g[col] - g.c); bruto = g[col]
            filas.append(dict(k=k, regla=nom, mercado=sim, ops=x.count(), bruto=bruto.mean(), neto=x.mean(), t=t(x),
                              neto_2012_19=x[g.fecha.dt.year <= 2019].mean(), neto_2020_26=x[g.fecha.dt.year >= 2020].mean()))
res = pd.DataFrame(filas); res.to_csv(B + "choques_resumen.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
print(res.round(3).to_string(index=False))
e = d[d.z >= 4]; e = e.assign(n=e.r30 - e.c, n2=e.r30 - 2 * e.c)
p = e.groupby("fecha").n.mean(); h = p.index[len(p) // 2]
print(f"\nPRINCIPAL cartera k4/30: días {len(p)} R/día {p.mean():+.3f} t {t(p):.2f} | 1ª mitad {p[:h].mean():+.3f} 2ª {p[h:].mean():+.3f} | x2 {e.groupby('fecha').n2.mean().mean():+.3f}")
j = pd.concat([p, orb], axis=1, join="inner").dropna(); print("corr con ORB:", round(j.corr().iloc[0, 1], 3), len(j))
print("por año:", e.groupby(e.fecha.dt.year).n.mean().round(3).to_dict())
