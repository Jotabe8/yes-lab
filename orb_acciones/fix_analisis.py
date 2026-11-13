"""Reversión tras el fix de Londres (preregistro PREREGISTRO_FIX.md)."""
import glob, numpy as np, pandas as pd
df = pd.concat(pd.read_csv(f) for f in glob.glob("orb_acciones/fix/*.csv"))
df["fecha"] = pd.to_datetime(df.fecha)
COM = 0.35
filas, cesta = [], {}
for ven, (a0, a1, e, xs) in {"fix": ("1530", "1600", "1605", {"V1": "1630", "V2": "1700"}),
                            "placebo": ("1130", "1200", "1205", {"V1": "1230", "V2": "1300"})}.items():
    for sim, g in df.groupby("sim"):
        g = g.sort_values("fecha").set_index("fecha")
        sig = np.log(g["p" + a1] / g["p" + a0])
        filt = sig.abs() > sig.abs().rolling(60, min_periods=20).median().shift(1)
        d = -np.sign(sig)
        for v, x in {**xs, "V3": xs["V2"]}.items():
            bruto = d * np.log(g["p" + x] / g["p" + e]) * 1e4
            coste = (g["s" + e] / 2 / g["p" + e] + g["s" + x] / 2 / g["p" + x]) * 1e4 + COM
            r = pd.DataFrame({"bruto": bruto, "coste": coste})
            if v == "V3":
                r = r[filt]
            r = r.dropna(); r = r[r.bruto.abs() < 300]
            r["neto"] = r.bruto - r.coste
            cesta.setdefault((ven, v), []).append(r.assign(sim=sim))
def t(x): return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
orb = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
res = []
for (ven, v), lst in cesta.items():
    r = pd.concat(lst)
    for per, m in (("2012-22", r.index.year <= 2022), ("2023-26", r.index.year >= 2023)):
        q = r[m]
        dia = q.groupby(level=0)[["bruto", "neto", "coste"]].mean()
        porpar = q.groupby("sim").bruto.mean()
        c = dia.neto.to_frame().join(orb, how="inner")
        res.append(dict(ventana=ven, var=v, periodo=per, dias=len(dia), ops=len(q),
                        bruto_pb=dia.bruto.mean(), coste_pb=dia.coste.mean(), neto_pb=dia.neto.mean(),
                        t_bruto=t(dia.bruto), t_neto=t(dia.neto), pares_pos=int((porpar > 0).sum()),
                        corr_orb=c.neto.corr(c.R) if len(c) > 30 else np.nan))
        if ven == "fix" and v == "V2":
            print(per, "por par bruto pb:", porpar.round(2).to_dict())
out = pd.DataFrame(res)
pd.set_option("display.width", 200)
print(out.round(3).to_string(index=False))
out.to_csv("orb_acciones/fix_resumen.csv", index=False)
r = pd.concat(cesta[("fix", "V2")]); print("por año bruto V2:", r.groupby(r.index.year).bruto.mean().round(2).to_dict())
