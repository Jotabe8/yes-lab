import pandas as pd, numpy as np
COSTE = {"US100": 1.0, "US500": 0.5, "US30": 2.5, "US2000": 0.5}
def cargar(sim):
    dirs = ["indices_2012", "indices"] if sim != "US2000" else ["indices"]
    b = pd.concat([pd.read_csv(f"orb_acciones/{x}/{sim}_b30.csv") for x in dirs]); b["fecha"] = pd.to_datetime(b.fecha)
    b = b.drop_duplicates(["fecha", "bar"])
    cv = pd.concat([pd.read_csv(f"orb_acciones/{x}/{sim}_convexo.csv") for x in dirs]); cv["fecha"] = pd.to_datetime(cv.fecha)
    cv = cv.drop_duplicates(["fecha", "k"])
    O = b.pivot(index="fecha", columns="bar", values="o"); C = b.pivot(index="fecha", columns="bar", values="c")
    H = b.pivot(index="fecha", columns="bar", values="h"); L = b.pivot(index="fecha", columns="bar", values="l")
    dia = pd.DataFrame({"o": O[0], "c": C[12], "h": H.max(axis=1), "l": L.min(axis=1)})
    dia["pc"] = dia.c.shift(1); dia["ret1"] = np.log(dia.c / dia.pc).shift(1)
    dia["ret5"] = np.log(dia.c.shift(1) / dia.c.shift(6)); dia["ret20"] = np.log(dia.c.shift(1) / dia.c.shift(21))
    dia["gap"] = np.log(dia.o / dia.pc)
    tr = pd.concat([dia.h - dia.l, (dia.h - dia.pc).abs(), (dia.l - dia.pc).abs()], axis=1).max(axis=1)
    dia["atr14"] = tr.rolling(14).mean().shift(1); dia["atr60"] = tr.rolling(60).mean().shift(1)
    dia["rng1"] = ((dia.h - dia.l) / dia.atr14).shift(1)
    dia["pos1"] = ((dia.c - dia.l) / (dia.h - dia.l)).shift(1)
    filas = []
    for k in range(1, 12):
        ent = O[k]
        hk = H.loc[:, :k - 1].max(axis=1); lk = L.loc[:, :k - 1].min(axis=1)
        f = pd.DataFrame({"k": k, "mov": np.log(ent / O[0]) , "movatr": (ent - O[0]) / dia.atr14,
                          "ult": np.log(ent / O[k - 1]), "rngk": (hk - lk) / dia.atr14, "posk": (ent - lk) / (hk - lk + 1e-9),
                          "ent": ent}, index=O.index)
        filas.append(f)
    X = pd.concat(filas).reset_index().merge(dia[["ret1", "ret5", "ret20", "gap", "atr14", "atr60", "rng1", "pos1"]].reset_index(), on="fecha")
    X["gapatr"] = X.gap * X.ent / X.atr14; X["volreg"] = X.atr14 / X.atr60; X["atrpct"] = X.atr14 / X.ent
    X["dow"] = X.fecha.dt.weekday
    X = X.merge(cv[["fecha", "k", "atr", "r_L15", "c_L15", "r_S15", "c_S15"]], on=["fecha", "k"])
    cmin = COSTE[sim] / (0.15 * X.atr)
    X["yL"] = X.r_L15 - np.maximum(X.c_L15, cmin); X["yS"] = X.r_S15 - np.maximum(X.c_S15, cmin)
    X["sim"] = sim
    return X.dropna(subset=["atr14", "atr60", "ret20", "yL", "yS"])
def todo():
    X = pd.concat([cargar(s) for s in ("US100", "US500", "US30", "US2000")])
    # cruzado: movimiento de US100 y US2000 en el mismo momento
    piv = X.pivot_table(index=["fecha", "k"], columns="sim", values="movatr")
    piv.columns = ["x_" + c for c in piv.columns]
    return X.merge(piv.reset_index(), on=["fecha", "k"], how="left")
