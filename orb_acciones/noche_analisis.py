"""Deriva nocturna 1:00→4:00 NY. Ver PREREGISTRO_NOCHE.md."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).parent
x = pd.concat([pd.read_csv(f, parse_dates=["fecha"]) for f in glob.glob(str(D / "noche/*.csv"))])
x = x[x.fecha.dt.dayofweek < 5].sort_values(["sim", "fecha"])
orb = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
t = lambda s: s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan
filas = []
for sim, g in x.groupby("sim"):
    g = g.set_index("fecha")
    pc = g.p1559.shift(1)
    tr = pd.concat([g.h - g.l, (g.h - pc).abs(), (g.l - pc).abs()], axis=1).max(axis=1)
    g["atr"] = tr.rolling(14).mean().shift(1)
    g["ses_prev"] = (g.p1559 / g.p0930 - 1).shift(1)
    u = 0.25 * g.atr
    for nom, e, s_ in (("noche 1-4", "0100", "0400"), ("placebo 12-15", "1200", "1500")):
        r = (g["p" + s_] - g["p" + e]) / u
        c = (g["s" + e] / 2 + g["s" + s_] / 2) / u
        pb = (g["p" + s_] / g["p" + e] - 1) * 1e4
        df = pd.DataFrame({"r": r, "c": c, "pb": pb, "prev": g.ses_prev}).dropna()
        for var, m in (("V1 todos", df.prev == df.prev), ("V2 tras caída", df.prev < 0)):
            h = df[m]
            for per, q in (("2012-22", h.index < "2023"), ("2023-26", h.index >= "2023")):
                k = h[q]; n = k.r - k.c
                cor = n.to_frame("n").join(orb, how="inner").corr().iloc[0, 1] if per == "2023-26" else np.nan
                filas.append(dict(sim=sim, ventana=nom, variante=var, periodo=per, ops=len(k), pb_bruto=k.pb.mean(),
                                  r_bruto=k.r.mean(), coste=k.c.mean(), neto=n.mean(), t_neto=t(n), t_bruto=t(k.r), corr_orb=cor))
                if nom.startswith("noche"):
                    n.to_csv(D / f"noche_{sim}_{var.split()[0]}_{per}.csv")
T = pd.DataFrame(filas)
print(T.round(3).to_string(index=False))
T.to_csv(D / "noche_resumen.csv", index=False)
