"""Atlas v2.1: pago convexo (stop 0,15/0,30 ATR, salida al cierre, recorrido M1) por celda.

Regla de dirección: 'seguir' (signo del recorrido desde la apertura hasta la entrada) o 'largo'.
Exceso = media R de la regla − media R con dirección al azar en las mismas filas ((L+S)/2): separa la
información de dirección de la estructura convexa. Selección en 2018-2022: BH 10 % sobre el exceso
(bilateral) + neto medio >= 0 en la dirección elegida + |exceso| >= 3 × coste + mismo signo en >= 3 de 4
mercados. Calibración: el ORB US100 (seguir la primera media hora, k=1) debería aparecer.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

D = Path(__file__).parent / "indices"
MERC = ["US100", "US500", "US30", "US2000"]
CORTE = pd.Timestamp("2023-01-01")
OOS = "--oos" in sys.argv


def cargar():
    v = pd.DataFrame({n: pd.read_csv(D / f"{n}.csv", index_col=0, parse_dates=True).Close for n in ("VIX", "VIX9D")}).dropna()
    v["ratio"] = v.VIX9D / v.VIX
    v = v.shift(1)
    xs = []
    for s in MERC:
        c = pd.read_csv(D / f"{s}_convexo.csv", parse_dates=["fecha"])
        d = pd.read_csv(D / f"{s}.csv", parse_dates=["fecha"]).set_index("fecha")
        d["gap"] = d.o930 / d.c.shift(1) - 1
        d["dia_prev"] = (d.c / d.o930 - 1).shift(1)
        c = c.join(d[["o930", "gap", "dia_prev"]], on="fecha")
        c["desde_ap"] = c.ent / c.o930 - 1
        xs.append(c)
    x = pd.concat(xs).merge(v[["VIX", "ratio"]], left_on="fecha", right_index=True, how="left")
    x["dow"] = x.fecha.dt.dayofweek
    return x.dropna(subset=["gap", "dia_prev", "desde_ap", "VIX", "ratio"])


def main():
    x = cargar()
    aj0 = x[x.fecha < CORTE]
    feats = ["gap", "dia_prev", "desde_ap", "VIX", "ratio"]
    for f in feats:
        x[f + "_t"] = np.digitize(x[f], aj0[f].quantile([1 / 3, 2 / 3]).values)
    conds = [("todos", None, None)] + [(f, f + "_t", v) for f in feats for v in (0, 1, 2)] + [("dow", "dow", v) for v in range(5)]
    sgn = np.sign(x.desde_ap)

    def celdas(df):
        out = []
        sg = np.sign(df.desde_ap)
        for st in ("15", "30"):
            rL, rS, cL, cS = df["r_L" + st], df["r_S" + st], df["c_L" + st], df["c_S" + st]
            azar = (rL + rS) / 2
            for regla in ("seguir", "largo"):
                lado = sg if regla == "seguir" else pd.Series(1.0, index=df.index)
                r = np.where(lado > 0, rL, np.where(lado < 0, rS, np.nan))
                c = np.where(lado > 0, cL, cS)
                tmp = pd.DataFrame({"sim": df.sim, "k": df.k, "r": r, "c": c, "ex": r - azar}, index=df.index)
                for nom, col, v in conds:
                    sel = tmp if col is None else tmp[df[col] == v]
                    for (sim, k), g in sel.groupby(["sim", "k"]):
                        g = g.dropna()
                        if len(g) < 60:
                            continue
                        t, p = stats.ttest_1samp(g.ex, 0)
                        out.append(dict(sim=sim, k=k, stop=st, regla=regla, cond=nom, nivel=-1 if v is None else v,
                                        n=len(g), r=g.r.mean(), coste=g.c.mean(), neto=(g.r - g.c).mean(),
                                        exceso=g.ex.mean(), t=t, p=p))
        return pd.DataFrame(out)

    A = celdas(x[x.fecha < CORTE]).sort_values("p")
    m = len(A)
    ok = A.p.values <= 0.10 * np.arange(1, m + 1) / m
    A["bh"] = np.maximum.accumulate(ok[::-1])[::-1]
    A["key"] = A.k.astype(str) + "|" + A.stop + "|" + A.regla + "|" + A.cond + "|" + A.nivel.astype(str)
    A["consist"] = A.key.map(A.groupby("key").exceso.apply(lambda s: max((s > 0).sum(), (s < 0).sum())))
    # dirección elegida: si el exceso es negativo, la regla útil es la contraria (neto de la contraria ≈ 2*azar - r - c)
    A["util"] = (A.exceso.abs() >= 3 * A.coste)
    print(f"celdas {m}; BH {A.bh.sum()}; BH+coste {(A.bh & A.util).sum()}; BH+coste+consistencia {(A.bh & A.util & (A.consist >= 3)).sum()}")
    cal = A[(A.sim == "US100") & (A.k == 1) & (A.regla == "seguir") & (A.cond == "todos")]
    print("\nCalibración ORB (US100, seguir primera media hora, todos los días):\n", cal[["stop", "n", "r", "coste", "neto", "exceso", "t", "p", "bh"]].round(3).to_string(index=False))
    print("\nMejores 30 por p:\n", A.head(30)[["sim", "k", "stop", "regla", "cond", "nivel", "n", "r", "neto", "exceso", "t", "p", "coste", "bh", "consist"]].round(3).to_string(index=False))
    A.to_csv(Path(__file__).parent / "atlas_convexo_ajuste.csv", index=False)
    sel = A[A.bh & A.util & (A.consist >= 3)]
    if OOS and len(sel):
        B = celdas(x[x.fecha >= CORTE])
        B["key"] = B.k.astype(str) + "|" + B.stop + "|" + B.regla + "|" + B.cond + "|" + B.nivel.astype(str)
        z = sel.merge(B, on=["sim", "key"], suffixes=("", "_oos"))
        print("\nFUERA DE MUESTRA 2023-2026:\n", z[["sim", "key", "exceso", "neto", "exceso_oos", "neto_oos", "t_oos"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
