import glob, numpy as np, pandas as pd
d = pd.concat(pd.read_csv(f) for f in glob.glob("orb_acciones/orb_var/*.csv")); d["fecha"] = pd.to_datetime(d.fecha)
orb = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
rows = []; series = {}
for sim, g in d.groupby("sim"):
    g = g.set_index("fecha").sort_index()
    for v in ["r5", "r10", "r15", "r30", "r60", "sar"]:
        if v not in g: continue
        spr = g["spr_sar" if v == "sar" else "spr" + v[1:]]
        r = g[v]; neto = r; neto2 = r - 0.6 * spr; bruto = r + spr
        series[(sim, v)] = r.dropna()
        for per, m in (("2012-17", g.index.year <= 2017), ("2018-22", (g.index.year >= 2018) & (g.index.year <= 2022)), ("2012-22", g.index.year <= 2022), ("2023-26", g.index.year >= 2023)):
            x = r[m].dropna()
            c = x.to_frame("x").join(orb, how="inner")
            rows.append(dict(sim=sim, var=v, per=per, ops=len(x), bruto=bruto[m].mean(), neto=x.mean(), t=t(x), neto_x2=neto2[m].mean(), corr_v018=c.x.corr(c.R) if len(c) > 30 else np.nan))
res = pd.DataFrame(rows); pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
print(res.round(3).to_string(index=False)); res.to_csv("orb_acciones/orb_variantes_resumen.csv", index=False)
# correlaciones entre variantes de US100 y con r10 (réplica)
u = pd.DataFrame({v: series[("US100", v)] for v in ["r5", "r10", "r15", "r30", "r60", "sar"] if ("US100", v) in series})
print(u.fillna(0).corr().round(2))
for s in ("US500", "US30"):
    if (s, "r10") in series:
        j = pd.concat([series[("US100", "r10")], series[(s, "r10")]], axis=1).dropna(); print(s, "corr r10 con US100", round(j.corr().iloc[0, 1], 2))
