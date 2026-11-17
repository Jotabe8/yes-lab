"""v15: utilidades comunes (carga de matrices M1, barajado para la prueba del motor, estadísticos)."""
import glob, os
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
COSTE = {"US100": 0.000049, "US500": 0.00008, "US30": 0.00005, "GER40": 0.000052}

def cargar(sim):
    fs = sorted(glob.glob(f"{AQUI}/datos/{sim}_*.npz"))
    F, X = [], []
    for f in fs:
        z = np.load(f)
        if len(z["fechas"]): F.append(z["fechas"]); X.append(z["x"])
    F = np.concatenate(F); X = np.concatenate(X).astype(np.float64)
    # rellenar huecos de minutos: O=H=L=C = cierre anterior
    for d in range(len(X)):
        x = X[d]; c = pd.Series(x[:, 3]).ffill().bfill().values
        m = np.isnan(x[:, 3])
        x[m, 0] = x[m, 1] = x[m, 2] = x[m, 3] = c[m]
    return pd.to_datetime(F), X

def barajar(Xs, semilla):
    """Baraja los días dentro de cada minuto del día (misma permutación para todos los mercados de Xs,
    así se conserva la correlación simultánea) y centra el rendimiento de cada minuto: martingala."""
    rng = np.random.default_rng(semilla)
    D, N, _ = Xs[0].shape
    perm = np.stack([rng.permutation(D) for _ in range(N)], 1)  # D x N
    sal = []
    for X in Xs:
        o, h, l, c = (X[:, :, k] for k in range(4))
        cprev = np.concatenate([o[:, :1], c[:, :-1]], 1)
        hueco = np.log(o / cprev); lh, ll, lc = np.log(h / o), np.log(l / o), np.log(c / o)
        cols = np.arange(N)[None, :]
        hueco, lh, ll, lc = (a[perm, cols] for a in (hueco, lh, ll, lc))
        hueco = hueco - (hueco + lc).mean(0, keepdims=True)
        base = np.log(o[:, :1])  # cada día empieza en su apertura real
        lo = base + np.cumsum(hueco, 1) + np.concatenate([np.zeros((D, 1)), np.cumsum(lc, 1)[:, :-1]], 1)
        Y = np.stack([np.exp(lo), np.exp(lo + lh), np.exp(lo + ll), np.exp(lo + lc)], 2)
        sal.append(Y)
    return sal

def tstat(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

def diario(df, col):
    return df.groupby("fecha")[col].mean()

def orb():
    s = pd.read_csv("/mnt/project-files/donde-operar/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
    return s

def resumen(df, col, coste="coste"):
    """df con fecha, col (R bruta), coste. Devuelve dict de estadísticos de la cartera diaria neta."""
    if len(df) < 3: return dict(ops=len(df))
    d = df.assign(n=df[col] - df[coste], n2=df[col] - 2 * df[coste])
    g = d.groupby("fecha")[["n", "n2", col]].mean()
    mitad = g.index[len(g) // 2]
    o = orb(); com = g.index.intersection(o.index)
    return dict(ops=len(d), dias=len(g), bruto=d[col].mean(), neto=d.n.mean(), t=tstat(g.n),
                m1=g.n[g.index < mitad].mean(), m2=g.n[g.index >= mitad].mean(), x2=g.n2.mean(),
                coste=d[coste].mean(), corr_orb=np.corrcoef(g.n.loc[com], o.loc[com])[0, 1] if len(com) > 30 else np.nan)
