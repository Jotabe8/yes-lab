"""P1-P2 (y P3 solo con --oos) del ORB de 5 min en acciones "en juego". Ver PREREGISTRO.md."""
import sys, glob
from pathlib import Path
import numpy as np, pandas as pd

D = Path(__file__).parent
COM = 0.00004
CORTE = pd.Timestamp("2023-01-01")
OOS = "--oos" in sys.argv


def cargar():
    df = pd.concat([pd.read_csv(f) for f in glob.glob(str(D / "datos/*.csv"))], ignore_index=True)
    df["fecha"] = pd.to_datetime(df.fecha)
    df = df.sort_values(["sim", "fecha"])
    prev = df.groupby("sim").vol5.transform(lambda s: s.shift(1).rolling(14).mean())
    df["vr"] = df.vol5 / prev
    return df[df.fecha >= "2018-02-01"].dropna(subset=["vr", "atr14"])


def ops_de(df, stop, lado_por_fila):
    """Devuelve operaciones para las filas dadas con el lado (+1/-1) indicado."""
    out = []
    for lado, s in ((1, "L"), (-1, "S")):
        x = df[(lado_por_fila == lado) & (df[f"trig_{s}"] == 1)].dropna(subset=[f"r_{stop}_{s}"])
        coste = (x[f"spr_ent_{s}"] / 2 + x[f"spr_sal_{stop}_{s}"] / 2 + 2 * COM * x[f"ent_{s}"]) / x[f"dist_{stop}_{s}"]
        out.append(pd.DataFrame({"fecha": x.fecha, "sim": x.sim, "r_bruto": x[f"r_{stop}_{s}"], "coste_r": coste,
                                 "vr": x.vr}))
    return pd.concat(out).sort_values("fecha")


def seleccion(df, filtro):
    x = df[df.dir != 0]
    if filtro == "vr2":
        x = x[x.vr >= 2].sort_values("vr", ascending=False).groupby("fecha").head(5)
    return x


def resumen(o, nombre):
    n = o.r_bruto - o.coste_r
    t = n.mean() / n.std() * np.sqrt(len(n)) if len(n) > 2 else np.nan
    return dict(variante=nombre, ops=len(o), ops_año=len(o) / max((o.fecha.max() - o.fecha.min()).days / 365.25, 1e-9),
                bruto=o.r_bruto.mean(), coste=o.coste_r.mean(), neto=n.mean(), t_neto=t,
                neto_x2=(o.r_bruto - 2 * o.coste_r).mean(), gana=(o.r_bruto > 0).mean())


def main():
    df = cargar()
    print("acciones", df.sim.nunique(), "días-acción", len(df), df.fecha.min().date(), df.fecha.max().date())
    ajuste = df[df.fecha < CORTE]
    rng = np.random.default_rng(0)
    filas, placebos = [], {}
    for filtro in ("vr2", "todas"):
        sel = seleccion(ajuste, filtro)
        for stop in ("A", "B"):
            nombre = f"{filtro}_stop{stop}"
            o = ops_de(sel, stop, sel.dir)
            r = resumen(o, nombre)
            pl = []
            for _ in range(200):
                lado = pd.Series(rng.choice([-1, 1], len(sel)), index=sel.index)
                pl.append(ops_de(sel, stop, lado).r_bruto.mean())
            r["placebo_p95"] = np.percentile(pl, 95)
            r["placebo_media"] = np.mean(pl)
            filas.append(r)
            o["año"] = o.fecha.dt.year
            pa = o.assign(n=o.r_bruto - o.coste_r).groupby("año").n.agg(["count", "mean", "sum"])
            print(f"\n{nombre} por año (neto R/op):\n", pa.round(3).to_string())
            if filtro == "vr2":
                o.to_csv(D / f"ops_ajuste_{nombre}.csv", index=False)
    t = pd.DataFrame(filas)
    print("\nAJUSTE 2018-2022\n", t.round(3).to_string(index=False))
    t.to_csv(D / "p1_ajuste.csv", index=False)
    # contribución por VR (stop B, todas las acciones)
    sel = seleccion(ajuste, "todas")
    o = ops_de(sel, "B", sel.dir)
    o["tramo_vr"] = pd.cut(o.vr, [0, 0.8, 1.2, 2, 3, 100])
    print("\nstop B por tramo de VR:\n", o.groupby("tramo_vr", observed=True).agg(
        ops=("r_bruto", "size"), bruto=("r_bruto", "mean"), coste=("coste_r", "mean")).round(3).to_string())
    if OOS:
        fuera = df[df.fecha >= CORTE]
        res = []
        for filtro in ("vr2", "todas"):
            sel = seleccion(fuera, filtro)
            for stop in ("A", "B"):
                o = ops_de(sel, stop, sel.dir)
                res.append(resumen(o, f"{filtro}_stop{stop}"))
                o.to_csv(D / f"ops_oos_{filtro}_stop{stop}.csv", index=False)
        print("\nFUERA DE MUESTRA 2023-2026\n", pd.DataFrame(res).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
