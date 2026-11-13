"""Reversión intradía del hueco nocturno en acciones (neutral). Ver PREREGISTRO_HUECO.md."""
import sys, glob
from pathlib import Path
import numpy as np, pandas as pd

D = Path(__file__).parent
COM = 0.00004
N = 5
CORTE = pd.Timestamp("2023-01-01")
OOS = "--oos" in sys.argv


def cargar():
    df = pd.concat([pd.read_csv(f) for f in glob.glob(str(D / "datos/*_diario.csv"))], ignore_index=True)
    df["fecha"] = pd.to_datetime(df.fecha)
    df = df.sort_values(["sim", "fecha"])
    df["c_prev"] = df.groupby("sim").c1600.shift(1)
    gap_dias = df.groupby("sim").fecha.diff().dt.days
    df = df[(gap_dias <= 4)]  # evita huecos de datos
    df["hueco"] = df.o930 / df.c_prev - 1
    df = df[df.hueco.abs() < 0.5]
    df["hueco_rel"] = df.hueco - df.groupby("fecha").hueco.transform("median")
    return df


def cesta(df, entrada, orden=None, rng=None):
    pe, se = f"p{entrada}", f"s{entrada}"
    x = df.dropna(subset=[pe, "p1555", "hueco_rel"]).copy()
    x = x[x.groupby("fecha").sim.transform("size") >= 30]
    if rng is not None:
        x["clave"] = rng.random(len(x))
    else:
        x["clave"] = x.hueco_rel
    x["rk"] = x.groupby("fecha").clave.rank(method="first")
    x["n"] = x.groupby("fecha").clave.transform("size")
    largo = x[x.rk <= N]; corto = x[x.rk > x.n - N]
    ret = lambda y: y.p1555 / y[pe] - 1
    cost = lambda y: (y[se] / 2 / y[pe] + y.s1555 / 2 / y.p1555 + 2 * COM)
    bruto = ret(largo).groupby(largo.fecha).mean() / 2 - ret(corto).groupby(corto.fecha).mean() / 2
    coste = cost(largo).groupby(largo.fecha).mean() / 2 + cost(corto).groupby(corto.fecha).mean() / 2
    return pd.DataFrame({"bruto": bruto, "coste": coste}).dropna()


def resumen(c, nombre):
    n = c.bruto - c.coste
    return dict(variante=nombre, dias=len(c), bruto_pb=c.bruto.mean() * 1e4, coste_pb=c.coste.mean() * 1e4,
                neto_pb=n.mean() * 1e4, t_neto=n.mean() / n.std() * np.sqrt(len(n)),
                neto_x2_pb=(c.bruto - 2 * c.coste).mean() * 1e4, sharpe_anual=n.mean() / n.std() * np.sqrt(252))


def main():
    df = cargar()
    print("acciones", df.sim.nunique(), "días", df.fecha.nunique())
    aj = df[df.fecha < CORTE]
    rng = np.random.default_rng(0)
    filas = []
    for ent in ("935", "931"):
        c = cesta(aj, ent)
        r = resumen(c, f"entrada {ent}")
        pl = [cesta(aj, ent, rng=rng).bruto.mean() * 1e4 for _ in range(200)]
        r["placebo_p95_pb"], r["placebo_media_pb"] = np.percentile(pl, 95), np.mean(pl)
        filas.append(r)
        pa = (c.bruto - c.coste).groupby(c.index.year).agg(["count", "mean"])
        pa["mean"] *= 1e4
        print(f"\nentrada {ent} neto por año (pb/día):\n", pa.round(2).to_string())
        c.to_csv(D / f"hueco_ajuste_{ent}.csv")
    print("\nAJUSTE 2018-2022\n", pd.DataFrame(filas).round(3).to_string(index=False))
    # tramos: cuánto revierte según tamaño del hueco relativo (toda la muestra de ajuste)
    x = aj.dropna(subset=["p935", "p1555"]).copy()
    x["intradia"] = x.p1555 / x.p935 - 1
    x["intradia_rel"] = x.intradia - x.groupby("fecha").intradia.transform("median")
    x["tramo"] = pd.qcut(x.hueco_rel, 10, labels=False)
    print("\nintradía relativo (pb) por decil de hueco relativo:\n",
          (x.groupby("tramo").intradia_rel.mean() * 1e4).round(1).to_string())
    if OOS:
        fuera = df[df.fecha >= CORTE]
        res = [resumen(cesta(fuera, e), f"entrada {e}") for e in ("935", "931")]
        print("\nFUERA DE MUESTRA 2023-2026\n", pd.DataFrame(res).round(3).to_string(index=False))
        cesta(fuera, "935").to_csv(D / "hueco_oos_935.csv")


if __name__ == "__main__":
    main()
