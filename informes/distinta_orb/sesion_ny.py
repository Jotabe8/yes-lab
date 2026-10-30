# Dirección de la sesión de NY (9:30 → 15:59 NY) predicha con información de otros mercados a las 9:30.
# Uso: python3 sesion_ny.py [oos]
import pandas as pd, numpy as np, sys
OOS = len(sys.argv) > 1 and sys.argv[1] == "oos"
rng = np.random.default_rng(1)

def b30(k):
    try: return pd.read_pickle(f"b30_{k}.pkl")
    except FileNotFoundError: return pd.read_pickle(f"../../busqueda/bars30/{k}.pkl")

def en(b, hhmm, col):                                       # valor de una barra fija cada día
    s = b[b.index.strftime("%H:%M") == hhmm][col]; s.index = s.index.normalize(); return s

def noche(k):                                               # 22:30 (cierre de la barra) del día anterior → 16:30
    b = b30(k); c0 = en(b, "22:30", "close").shift(1); c1 = en(b, "16:00", "close")
    return np.log(c1 / c0.reindex(c1.index, method="ffill"))

ger = b30("GER40"); f_ger = np.log(en(ger, "16:00", "close") / en(ger, "10:00", "open"))
comunes = {"oro": noche("XAUUSD"), "jpy": noche("USDJPY"), "eur": noche("EURUSD"), "ger": f_ger,
           "rty_ndx": noche("US2000") - noche("US100")}

def datos(k):
    b = b30(k)
    o, c, sp = en(b, "16:30", "open"), en(b, "22:30", "close"), en(b, "16:30", "spread")
    y = np.log(c / o)
    X = pd.DataFrame({"noche": noche(k), "ayer": y.shift(1), **comunes})
    d = pd.concat([X, y.rename("y"), (sp / o * 1e4).rename("coste")], axis=1)
    d = d[d.index.dayofweek < 5].dropna()
    return d[d.index >= "2019-01-01"]

def predice(X, y, cada=20, minimo=250, lam=1.0):
    p = pd.Series(np.nan, index=X.index)
    for i in range(minimo, len(X), cada):
        Xt, yt = X.iloc[:i].values, y.iloc[:i].values
        mu, sd = Xt.mean(0), Xt.std(0) + 1e-12
        Z = (Xt - mu) / sd
        w = np.linalg.solve(Z.T @ Z + lam * len(Z) * np.eye(Z.shape[1]) * 0.01, Z.T @ (yt - yt.mean()))
        Zf = (X.iloc[i:i + cada].values - mu) / sd
        p.iloc[i:i + cada] = Zf @ w + yt.mean()
    return p

filas = []
for k in ["US100", "US500", "US30", "US2000"]:
    d = datos(k)
    X, y = d.drop(columns=["y", "coste"]), d.y
    p = predice(X, y)
    m = p.notna() & ((d.index >= "2023-01-01") if OOS else (d.index < "2023-01-01"))
    g = (np.sign(p) * y * 1e4)[m]
    pl = []
    for _ in range(100):
        Xs = X.copy(); Xs[:] = X.values[rng.permutation(len(X))]
        ps = predice(Xs, y)
        pl.append((np.sign(ps) * y * 1e4)[m].mean())
    largo = (y * 1e4)[m].mean()
    filas.append(dict(mercado=k, ops=int(m.sum()), bruto_pb=g.mean(), t=g.mean() / g.std() * np.sqrt(len(g)),
                      coste_pb=d.coste[m].mean(), placebo_p95=np.percentile(pl, 95), siempre_largo_pb=largo,
                      mov_pb=(y.abs() * 1e4)[m].mean(), pct_largos=(p[m] > 0).mean(),
                      por_anio=g.groupby(g.index.year).mean().round(1).to_dict()))
    print(filas[-1], flush=True)
pd.DataFrame(filas).to_csv("sesion_ny_oos.csv" if OOS else "sesion_ny_ajuste.csv", index=False)
