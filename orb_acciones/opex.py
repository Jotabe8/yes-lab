import pandas as pd, numpy as np
fil = []
for sim in ("US100", "US500", "US30"):
    b = pd.concat([pd.read_csv(f"orb_acciones/indices_2012/{sim}_b30.csv"), pd.read_csv(f"orb_acciones/indices/{sim}_b30.csv")])
    b["fecha"] = pd.to_datetime(b.fecha); b = b.drop_duplicates(["fecha", "bar"])
    p = b.pivot(index="fecha", columns="bar", values="o"); c = b.pivot(index="fecha", columns="bar", values="c")
    s = b.pivot(index="fecha", columns="bar", values="spr")
    d = pd.DataFrame({"mov": np.log(p[5] / p[0]), "ret": np.log(c[12] / p[5]), "spr": (s[5] / p[5]).fillna(0)}).dropna()
    d["bruto"] = -np.sign(d.mov) * d.ret * 1e4
    d["coste"] = d.spr * 1e4 + 0.5 / p[5].reindex(d.index) * 1e4 * 0  # spread Dukascopy ya en spr; >=2018
    d.loc[d.index.year < 2018, "coste"] = 1.0 / p[5].reindex(d.index)[d.index.year < 2018] * 1e4 * (0.6 if sim != "US100" else 1)
    d["neto"] = d.bruto - d.coste
    dt = d.index
    d["opex"] = (dt.weekday == 4) & (dt.day >= 15) & (dt.day <= 21)
    d["vie"] = dt.weekday == 4
    d["trim"] = d.opex & dt.month.isin([3, 6, 9, 12])
    d["sim"] = sim; fil.append(d)
d = pd.concat(fil)
def t(x): return x.mean() / x.std() * np.sqrt(len(x))
rows = []
for per, m in (("2012-22", d.index.year <= 2022), ("2023-26", d.index.year >= 2023)):
    for nom, mm in (("OPEX", d.opex), ("OPEX trimestral", d.trim), ("viernes no OPEX", d.vie & ~d.opex), ("resto días", ~d.vie)):
        q = d[m & mm].groupby(level=0)[["bruto", "coste", "neto"]].mean()
        rows.append(dict(periodo=per, grupo=nom, dias=len(q), bruto_pb=q.bruto.mean(), t_bruto=t(q.bruto), coste_pb=q.coste.mean(), neto_pb=q.neto.mean(), t_neto=t(q.neto)))
r = pd.DataFrame(rows); print(r.round(2).to_string(index=False)); r.to_csv("orb_acciones/opex_resumen.csv", index=False)
q = d[d.opex]; print(q.groupby([q.sim]).bruto.mean().round(1).to_dict()); print(q.groupby(q.index.year).bruto.mean().round(1).to_dict())
