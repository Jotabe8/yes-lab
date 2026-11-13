"""Amplitud de apertura (71 acciones) y movimiento estrecho/amplio de US100, US500, US30. Ver PREREGISTRO_AMPLITUD.md."""
import sys, glob
from pathlib import Path
import numpy as np, pandas as pd

D = Path(__file__).parent
CORTE = pd.Timestamp("2023-01-01")
OOS = "--oos" in sys.argv

acc = pd.concat([pd.read_csv(f, usecols=["fecha", "sim", "o5", "c5"]) for f in glob.glob(str(D / "datos/*.csv"))
                 if not f.endswith("_diario.csv")])
acc["fecha"] = pd.to_datetime(acc.fecha)
amp = acc.assign(up=acc.c5 > acc.o5).groupby("fecha").agg(B=("up", "mean"), n=("up", "size"))
amp = amp[amp.n >= 50]


def ops_indice(sim, modo, rng=None):
    x = pd.read_csv(D / f"indices/{sim}.csv", parse_dates=["fecha"]).set_index("fecha").sort_index()
    pc = x.c.shift(1)
    tr = pd.concat([x.h - x.l, (x.h - pc).abs(), (x.l - pc).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean().shift(1)
    x = x.join(amp, how="inner").dropna(subset=["o930", "p935", "p1555", "atr"])
    m = x.p935 / x.o930 - 1
    if modo == "estrecho":
        lado = np.where((m > 0) & (x.B < 0.4), -1, np.where((m < 0) & (x.B > 0.6), 1, 0))
    else:
        lado = np.where((m > 0) & (x.B > 0.6), 1, np.where((m < 0) & (x.B < 0.4), -1, 0))
    x["lado"] = lado
    x = x[x.lado != 0].copy()
    if rng is not None:
        x["lado"] = rng.choice([-1, 1], len(x))
    unidad = 0.25 * x.atr
    x["r_bruto"] = x.lado * (x.p1555 - x.p935) / unidad
    x["coste_r"] = (x.s935 / 2 + x.s1555 / 2) / unidad
    x["pb"] = x.lado * (x.p1555 / x.p935 - 1) * 1e4
    x["sim"] = sim
    return x.reset_index()[["fecha", "sim", "lado", "B", "r_bruto", "coste_r", "pb"]]


def res(o, nombre):
    n = o.r_bruto - o.coste_r
    return dict(variante=nombre, ops=len(o), ops_año=len(o) / 5, bruto=o.r_bruto.mean(), coste=o.coste_r.mean(),
                neto=n.mean(), t=n.mean() / n.std() * np.sqrt(len(n)), neto_x2=(o.r_bruto - 2 * o.coste_r).mean(),
                pb_bruto=o.pb.mean())


rng = np.random.default_rng(0)
filas = []
for modo in ("estrecho", "amplio"):
    for sim in ("US100", "US500", "US30"):
        o = ops_indice(sim, modo)
        a = o[o.fecha < CORTE]
        r = res(a, f"{modo} {sim}")
        pl = []
        for _ in range(200):
            p = ops_indice(sim, modo, rng)
            pl.append(p[p.fecha < CORTE].r_bruto.mean())
        r["placebo_p95"] = np.percentile(pl, 95)
        filas.append(r)
        pa = (a.r_bruto - a.coste_r).groupby(a.fecha.dt.year).agg(["count", "mean"])
        print(f"{modo} {sim} neto R por año:", " ".join(f"{y}:{v:+.2f}({c})" for y, (c, v) in pa.iterrows()))
        if OOS:
            b = o[o.fecha >= CORTE]
            filas.append(res(b, f"OOS {modo} {sim}"))
        o.to_csv(D / f"amplitud_{modo}_{sim}.csv", index=False)
print("\nAJUSTE 2018-2022 (R = 0,25 ATR14)\n", pd.DataFrame(filas).round(3).to_string(index=False))
