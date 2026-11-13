"""Atlas intradía condicionado (método nuevo, ver metodo/BUSQUEDA_V2.md).

Celdas = mercado × barra de entrada (30 min) × horizonte (siguiente barra / hasta el cierre) × condición
conocida al entrar. Se mide la rentabilidad media EN EXCESO sobre la misma ventana sin condición (para no
confundir la deriva alcista con señal), p-valor, y coste. Selección en ajuste 2018-2022 con
Benjamini-Hochberg (FDR 10 %) + |exceso| >= 3 x coste + mismo signo en >= 3 de 4 mercados.
Las supervivientes se miran UNA vez en 2023-2026 (--oos).
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

D = Path(__file__).parent / "indices"
MERC = ["US100", "US500", "US30", "US2000"]
CORTE = pd.Timestamp("2023-01-01")
OOS = "--oos" in sys.argv


def vix():
    v = {n: pd.read_csv(D / f"{n}.csv", index_col=0, parse_dates=True).Close for n in ("VIX", "VIX9D")}
    v = pd.DataFrame(v).dropna()
    v["ratio"] = v.VIX9D / v.VIX
    return v.shift(1)  # cierre del día anterior: conocido antes de la apertura


def panel(sim, vx):
    b = pd.read_csv(D / f"{sim}_b30.csv", parse_dates=["fecha"])
    b = b[b.n >= 25]
    o = b.pivot(index="fecha", columns="bar", values="o")
    c = b.pivot(index="fecha", columns="bar", values="c")
    s = b.pivot(index="fecha", columns="bar", values="spr")
    ok = o.notna().all(axis=1) & c.notna().all(axis=1) & (o.shape[1] == 13)
    o, c, s = o[ok], c[ok], s[ok]
    cierre = c[12]
    previo = cierre.shift(1)
    dia_prev = (cierre / o[0] - 1).shift(1)
    gap = o[0] / previo - 1
    filas = []
    for k in range(1, 12):
        desde_ap = o[k] / o[0] - 1
        barra_prev = c[k - 1] / o[k - 1] - 1
        for hz, fin in (("sig", c[k]), ("cierre", c[12])):
            r = (fin / o[k] - 1) * 1e4
            coste = (s[k] / 2 / o[k] + (s[k] if hz == "sig" else s[12]) / 2 / fin) * 1e4
            filas.append(pd.DataFrame({"fecha": o.index, "sim": sim, "k": k, "hz": hz, "r": r.values,
                                       "coste": coste.values, "gap": gap.values, "dia_prev": dia_prev.values,
                                       "desde_ap": desde_ap.values, "barra_prev": barra_prev.values}))
    x = pd.concat(filas)
    x = x.merge(vx[["VIX", "ratio"]], left_on="fecha", right_index=True, how="left")
    x["dow"] = x.fecha.dt.dayofweek
    return x.dropna()


def main():
    vx = vix()
    x = pd.concat([panel(m, vx) for m in MERC])
    aj = x[x.fecha < CORTE]
    feats = ["gap", "dia_prev", "desde_ap", "barra_prev", "VIX", "ratio"]
    cortes = {f: aj[f].quantile([1 / 3, 2 / 3]).values for f in feats}  # solo con ajuste
    for f in feats:
        x[f + "_t"] = np.digitize(x[f], cortes[f])
    conds = [("todos", None, None)] + [(f, f + "_t", v) for f in feats for v in (0, 1, 2)] + \
            [("dow", "dow", v) for v in range(5)]
    x["base"] = x.groupby(["sim", "k", "hz", x.fecha < CORTE]).r.transform("mean")
    aj = x[x.fecha < CORTE]

    def celdas(df):
        out = []
        for (sim, k, hz), g in df.groupby(["sim", "k", "hz"]):
            for nom, col, v in conds:
                h = g if col is None else g[g[col] == v]
                if len(h) < 60:
                    continue
                ex = h.r - (0 if col is None else h.base)
                t, p = stats.ttest_1samp(ex, 0)
                out.append(dict(sim=sim, k=k, hz=hz, cond=nom, nivel=v if v is not None else -1, n=len(h),
                                media=h.r.mean(), exceso=ex.mean(), t=t, p=p, coste=h.coste.mean()))
        return pd.DataFrame(out)

    A = celdas(aj)
    m = len(A)
    A = A.sort_values("p")
    A["bh"] = A.p.values <= 0.10 * np.arange(1, m + 1) / m
    A["bh"] = A.bh[::-1].cummax()[::-1]  # BH: todas hasta la última que pasa
    A["key"] = A.k.astype(str) + "|" + A.hz + "|" + A.cond + "|" + A.nivel.astype(str)
    signo = A.groupby("key").exceso.apply(lambda s: max((s > 0).sum(), (s < 0).sum()))
    A["consist"] = A.key.map(signo)
    A["util"] = A.exceso.abs() >= 3 * A.coste
    print(f"celdas {m}; pasan BH {A.bh.sum()}; BH+coste {(A.bh & A.util).sum()}; BH+coste+consistencia "
          f"{(A.bh & A.util & (A.consist >= 3)).sum()}")
    print("\nMejores 25 por p (ajuste 2018-2022):")
    print(A.head(25)[["sim", "k", "hz", "cond", "nivel", "n", "media", "exceso", "t", "p", "coste", "bh", "consist"]]
          .round(3).to_string(index=False))
    A.to_csv(Path(__file__).parent / "atlas_ajuste.csv", index=False)
    sel = A[A.bh & A.util & (A.consist >= 3)]
    sel.to_csv(Path(__file__).parent / "atlas_supervivientes.csv", index=False)
    if OOS and len(sel):
        B = celdas(x[x.fecha >= CORTE])
        B["key"] = B.k.astype(str) + "|" + B.hz + "|" + B.cond + "|" + B.nivel.astype(str)
        z = sel.merge(B, on=["sim", "key"], suffixes=("", "_oos"))
        z["mismo_signo"] = np.sign(z.exceso) == np.sign(z.exceso_oos)
        print("\nFUERA DE MUESTRA 2023-2026 de las supervivientes:")
        print(z[["sim", "key", "exceso", "t", "exceso_oos", "t_oos", "coste_oos", "mismo_signo"]].round(3).to_string(index=False))
        z.to_csv(Path(__file__).parent / "atlas_oos.csv", index=False)


if __name__ == "__main__":
    main()
