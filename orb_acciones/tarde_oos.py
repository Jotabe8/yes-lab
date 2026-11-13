"""Tendencia de tarde convexa: fuera de muestra 2023-2026 (abierto una vez) y correlación con el ORB US100."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).parent / "indices"
orb = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
filas = []
for s in ["US100", "US500", "US30", "US2000"]:
    c = pd.read_csv(D / f"{s}_convexo.csv", parse_dates=["fecha"])
    d = pd.read_csv(D / f"{s}.csv", parse_dates=["fecha"]).set_index("fecha")
    c = c.join(d.o930, on="fecha")
    sg = np.sign(c.ent / c.o930 - 1)
    c["r"] = np.where(sg > 0, c.r_L15, np.where(sg < 0, c.r_S15, np.nan))
    c["cst"] = np.where(sg > 0, c.c_L15, c.c_S15)
    c["cst_ftmo"] = c.cst * 0.6  # horquilla FTMO US100 ≈ 0,5-0,8 pb frente a ≈ 1,3 pb Dukascopy
    for k in (8, 10, 11):
        for per, q in (("2018-22", c.fecha < "2023"), ("2023-26", c.fecha >= "2023")):
            g = c[(c.k == k) & q].dropna(subset=["r"])
            n = g.r - g.cst
            ser = n.set_axis(g.fecha)
            cor = ser.to_frame("x").join(orb, how="inner").corr().iloc[0, 1]
            filas.append(dict(sim=s, k=k, periodo=per, ops=len(g), bruto=g.r.mean(), coste=g.cst.mean(),
                              neto=n.mean(), t=n.mean() / n.std() * np.sqrt(len(n)),
                              neto_ftmo=(g.r - g.cst_ftmo).mean(), gana=(g.r > 0).mean(), corr_orb=cor))
            if s == "US100" and k == 8:
                ser.to_csv(Path(__file__).parent / f"tarde_us100_k8_{per}.csv")
t = pd.DataFrame(filas)
print(t.round(3).to_string(index=False))
