"""Prueba preregistrada PREREGISTRO_ORB_GER40.md. Coste = 0,0052 % del precio (horquilla FTMO 9:00-10:00 Berlín)."""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v3/"
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(B + "orb_ger40/ger40_*.csv")))
d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index()
print("días", len(d), "con operación", d.r.notna().sum(), "| años", d.index.year.min(), "-", d.index.year.max())
d = d.dropna(subset=["r"])
c = 0.0052 / 100 * d.px / d.dist
S = {"bruto": d.r, "neto": d.r - c, "neto_x2": d.r - 2 * c, "be2_neto": d.r_be2 - c,
     "placebo_lado": d.r_contra - c, "placebo_hora": d.r_hora - c}
corte = pd.Timestamp("2019-07-01"); filas = []
for k, s in S.items():
    for per, msk in (("2012-19/06", s.index < corte), ("2019/07-26", s.index >= corte), ("2018-22", (s.index.year >= 2018) & (s.index.year <= 2022)),
                     ("2023-26", s.index.year >= 2023), ("total", s.index.year > 0)):
        y = s[msk].dropna(); filas.append(dict(serie=k, periodo=per, ops=len(y), R=y.mean(), t=t(y)))
res = pd.DataFrame(filas); res.to_csv(B + "orb_ger40_resumen.csv", index=False)
pd.set_option("display.width", 220)
print(res.pivot_table(index="serie", columns="periodo", values=["R", "t"], sort=False).round(3).to_string())
print("coste medio R", round(c.mean(), 4), "| horquilla Dukascopy en R", round((d.spr_duka_med / d.dist).mean(), 3))
n = S["neto"]
print("neto por año:", n.groupby(n.index.year).mean().round(3).to_dict())
print("ops/año:", n.groupby(n.index.year).size().to_dict())
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
j = pd.concat([n, orb], axis=1, join="inner").dropna(); print("corr con ORB US100 v018:", round(j.corr().iloc[0, 1], 3), "días", len(j))
ref = pd.read_csv("/mnt/project-files/probar-mt5/ORB_GER40_referencia_python.csv", parse_dates=["fecha"]).set_index("fecha")
ref["l"] = np.where(ref.lado == "LONG", 1, -1)
k = d[["lado", "r"]].join(ref.drop(columns="lado"), how="inner")
print(f"réplica vs referencia 2022-26: días comunes {len(k)} mismo lado {(k.lado == k.l).mean():.1%} corr R {k.r.corr(k.R_python):.2f}"
      f" | R réplica bruto {k.r.mean():+.3f} vs ref {k.R_python.mean():+.3f}")
p = {"t_neto": t(n), "2a_mitad": n[n.index >= corte].mean(), "x2": S["neto_x2"].mean(),
     "placebo_lado": S["placebo_lado"].mean(), "placebo_hora": S["placebo_hora"].mean(), "neto": n.mean()}
ok = p["t_neto"] >= 2.4 and p["2a_mitad"] > 0 and p["x2"] > 0 and p["neto"] > p["placebo_lado"] and p["neto"] > p["placebo_hora"] and abs(j.corr().iloc[0, 1]) < 0.3
print("VEREDICTO:", "PASA" if ok else "NO PASA", {k: round(v, 3) for k, v in p.items()})
