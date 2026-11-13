"""Prueba preregistrada (PREREGISTRO_ORB_ASIA.md). Coste = mediana de la horquilla real de FTMO en la
primera hora (spread_aperturas_ftmo.csv) aplicada al precio de entrada / distancia del stop."""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v3/"
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
SPR = {"JP225": 0.0157, "HK50": 0.0269, "AUS200": 0.0115}   # % mediana FTMO
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
cols = {}; filas = []
for sim in SPR:
    fs = sorted(glob.glob(B + f"orb_asia/asia_{sim}_*.csv"))
    if not fs: print("sin datos", sim); continue
    d = pd.concat(pd.read_csv(f) for f in fs); d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index()
    d = d.dropna(subset=["r"])
    c = SPR[sim] / 100 * d.px / d.dist
    ser = {"bruto": d.r, "neto": d.r - c, "neto_x2": d.r - 2 * c, "contra_neto": d.r_contra - c,
           "hora_neto": (d.r_hora - c) if "r_hora" in d else None}
    for k, s in ser.items():
        if s is None: continue
        cols[(sim, k)] = s
        for per, m in (("2018-22", s.index.year <= 2022), ("2023-26", s.index.year >= 2023), ("2018-26", s.index.year > 0)):
            y = s[m].dropna(); filas.append(dict(mercado=sim, serie=k, periodo=per, ops=len(y), R=y.mean(), t=t(y)))
    print(sim, "coste medio R", round(c.mean(), 3), "| Dukascopy horquilla R", round((d.spr_duka_med / d.dist).mean(), 3),
          "| neto por año:", d.r.sub(c).groupby(d.index.year).mean().round(2).to_dict())
res = pd.DataFrame(filas); res.to_csv(B + "orb_asia_resumen.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
print(res.pivot_table(index=["mercado", "serie"], columns="periodo", values=["R", "t"], sort=False).round(3).to_string())
def cart(k): return pd.concat([cols[(s, k)] for s in SPR if (s, k) in cols], axis=1, sort=True).mean(axis=1)
p = cart("neto"); h = p.index[len(p) // 2]
print(f"\nPRINCIPAL cartera Asia neto: días {len(p)} R/día {p.mean():+.3f} t {t(p):.2f} | 1ª mitad {p[:h].mean():+.3f} 2ª {p[h:].mean():+.3f}"
      f" | x2 {cart('neto_x2').mean():+.3f} | placebo lado {cart('contra_neto').mean():+.3f} | placebo hora {cart('hora_neto').mean():+.3f}")
j = pd.concat([p, orb], axis=1, join="inner", sort=True).dropna(); print("corr con ORB US100:", round(j.corr().iloc[0, 1], 3), len(j))
print("corr entre mercados:\n", pd.concat({s: cols[(s, 'neto')] for s in SPR if (s, 'neto') in cols}, axis=1, sort=True).corr().round(2))
p.rename("R").to_frame().to_csv(B + "orb_asia_cartera_diaria.csv")
