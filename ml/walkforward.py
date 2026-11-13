import sys, numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, "ml"); import datos
X = datos.todo(); X["anio"] = X.fecha.dt.year
X["simc"] = X.sim.astype("category").cat.codes
F = ["k", "mov", "movatr", "ult", "rngk", "posk", "ret1", "ret5", "ret20", "gapatr", "volreg", "atrpct", "rng1", "pos1", "dow", "simc", "x_US100", "x_US500", "x_US30", "x_US2000"]
P = dict(n_estimators=200, learning_rate=0.03, num_leaves=15, min_child_samples=400, subsample=0.7, subsample_freq=1, colsample_bytree=0.7, verbose=-1)
def correr(semilla=0, barajar=False):
    rng = np.random.default_rng(semilla); salida = []
    for Y in range(2016, 2027):
        tr = X[X.anio < Y]; te = X[X.anio == Y].copy()
        yl, ys = tr.yL.values.copy(), tr.yS.values.copy()
        if barajar:  # placebo: rompe la relación características-resultado por días
            dias = tr.fecha.unique(); perm = dict(zip(dias, rng.permutation(dias)))
            m = tr.assign(f2=tr.fecha.map(perm)).set_index(["f2", "sim", "k"])
            orig = tr.set_index(["fecha", "sim", "k"])[["yL", "yS"]]
            j = orig.reindex(m.index)
            yl, ys = j.yL.values, j.yS.values; ok = ~np.isnan(yl)
        else:
            ok = np.ones(len(tr), bool)
        ml = lgb.LGBMRegressor(random_state=semilla, **P).fit(tr[F][ok], yl[ok])
        ms = lgb.LGBMRegressor(random_state=semilla, **P).fit(tr[F][ok], ys[ok])
        te["pL"], te["pS"] = ml.predict(te[F]), ms.predict(te[F])
        te["p"] = te[["pL", "pS"]].max(axis=1); te["y"] = np.where(te.pL >= te.pS, te.yL, te.yS)
        best = te.sort_values("p").groupby(["fecha", "sim"]).tail(1)
        salida.append(best[["fecha", "sim", "k", "p", "y", "anio"]])
    return pd.concat(salida)
if __name__ == "__main__":
    r = correr()
    r.to_csv("ml/wf_real.csv", index=False)
    for thr in (0.0, 0.05, 0.1, 0.2):
        q = r[r.p > thr]
        print(f"umbral {thr}: ops {len(q)}, R media {q.y.mean():.3f}, t {q.y.mean()/q.y.std()*np.sqrt(len(q)):.2f}")
        print("   por año", q.groupby("anio").y.mean().round(2).to_dict())
        print("   por mercado", q.groupby("sim").y.agg(["count", "mean"]).round(3).to_dict())
