"""Comprobaciones informativas (no deciden) sobre V2 rango, después del veredicto preregistrado."""
import glob, os, numpy as np, pandas as pd
D = os.path.dirname(__file__)
COSTE = {"GER40": 0.0052, "UK100": 0.0079, "JP225": 0.0157, "XAUUSD": 0.0110, "USOIL": 0.0500, "US100": 0.0049}
C5 = ["GER40", "UK100", "JP225", "XAUUSD", "USOIL"]
df = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/datos/*.csv")]); df["fecha"] = pd.to_datetime(df.fecha)
df = df[(df.fecha >= "2012-03-01") & df.lado.notna()].copy()
df["n"] = df.r - df.sim.map(COSTE) / 100 * df.px / df.dist
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
c = df[df.sim.isin(C5)]
print("Umbral rrango  n  neto  t")
for u in [1.0, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5]:
    x = c[c.rrango >= u].n; print(f"  {u:.1f} {len(x):5d} {x.mean():+.3f} {t(x):5.2f}")
ej = c[c.rrango >= 1.5]
print("Mediana R neto", ej.n.median().round(3), "| % ganadoras", (ej.n > 0).mean().round(3))
for q in [0.99, 0.98, 0.95]:
    x = ej.n[ej.n < ej.n.quantile(q)]; print(f"Sin el {100*(1-q):.0f} % mejor: {x.mean():+.3f} t {t(x):.2f}")
print("Años con neto>0:", (ej.groupby(ej.fecha.dt.year).n.sum() > 0).sum(), "de", ej.fecha.dt.year.nunique())
print("Sin 2012:", round(ej[ej.fecha >= '2013-01-01'].n.mean(), 3), round(t(ej[ej.fecha >= '2013-01-01'].n), 2))
print("2018-2026 (periodo de v018):", round(ej[ej.fecha >= '2018-01-01'].n.mean(), 3), round(t(ej[ej.fecha >= '2018-01-01'].n), 2))
# sin USOIL (coste no medido) y solo los 3 mejores costes
for g in [["GER40", "UK100", "JP225", "XAUUSD"], ["GER40", "UK100", "XAUUSD"]]:
    x = ej[ej.sim.isin(g)].n; print("Solo", g, len(x), round(x.mean(), 3), round(t(x), 2))
dia = ej.groupby("fecha").n.sum(); bd = dia.reindex(pd.bdate_range("2012-03-01", "2026-11-13"), fill_value=0)
print("Sharpe anual cartera", round(bd.mean() / bd.std() * np.sqrt(252), 2), "| ops/año", round(len(ej) / 14.7, 1))
print("Ops por día con señal:", ej.groupby("fecha").size().value_counts().sort_index().to_dict())
cm = ej.pivot_table(index="fecha", columns="sim", values="n").corr().round(2); print(cm)
v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
j = pd.concat([bd.rename("v2"), v.rename("v018")], axis=1).loc["2018-01-23":"2026-11-13"].fillna(0)
for w in [0, 0.5, 1.0]:
    s = j.v018 + w * j.v2; print(f"v018 + {w}·V2: Sharpe {s.mean()/s.std()*np.sqrt(252):.2f}")
print("Corr mensual v018-V2:", round(j.resample("ME").sum().corr().iloc[0, 1], 2))
