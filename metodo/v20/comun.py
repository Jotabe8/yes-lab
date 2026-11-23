"""v20: carga de precio (matrices de v15), volumen (Dukascopy y ETF), VWAP de sesión y estadísticos."""
import glob, os, sys
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_sp = _iu.spec_from_file_location("v15comun", os.path.join(AQUI, "..", "v15", "comun.py"))
_m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
cargar_precio = _m.cargar
COSTE = {"US100": 0.69e-4, "GER40": 0.72e-4, "US500": 0.80e-4, "US30": 0.80e-4}
ETF = {"US100": "QQQ", "US500": "SPY", "US30": "DIA"}
MERCADOS = ["US100", "US500", "US30", "GER40"]
FIN_P1 = pd.Timestamp("2022-12-31")


def vol_duka(sim, fechas):
    fs = sorted(glob.glob(f"{AQUI}/datos/vol_{sim}_*.npz"))
    if not fs:
        return None
    d = {}
    for f in fs:
        z = np.load(f)
        for a, b in zip(z["fechas"], z["v"]):
            d[a] = b
    n = len(next(iter(d.values())))
    return np.stack([d.get(str(f.date()), np.full(n, np.nan)) for f in fechas]).astype(np.float64)


def vol_etf(sim, fechas):
    f = f"{AQUI}/datos/etf_{ETF.get(sim, 'x')}.npz"
    if not os.path.exists(f):
        return None
    z = np.load(f); d = dict(zip(z["fechas"], z["x"][:, :, 4]))
    return np.stack([d.get(str(x.date()), np.full(390, np.nan)) for x in fechas]).astype(np.float64)


def vwap(X, w):
    """VWAP y σ ponderada desde la apertura. w (D,N) con nan; días sin volumen -> TWAP."""
    p = X[:, :, 1:4].mean(2)
    if w is None:
        w = np.ones_like(p)
    w = np.nan_to_num(w, nan=0.0).clip(min=0)
    sin = w.sum(1) <= 0
    w = w.copy(); w[sin] = 1.0
    w = w + 1e-9 * w.mean(1, keepdims=True) + 1e-12
    cw = np.cumsum(w, 1); vw = np.cumsum(w * p, 1) / cw
    s2 = np.cumsum(w * p * p, 1) / cw - vw ** 2
    return vw, np.sqrt(np.clip(s2, 0, None)), sin


def atr(X, n=14):
    h, l, c = X[:, :, 1].max(1), X[:, :, 2].min(1), X[:, -1, 3]
    pc = np.r_[np.nan, c[:-1]]
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc))); tr[0] = h[0] - l[0]
    a = pd.Series(tr).rolling(n).mean().shift(1).values
    return a


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return (x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else np.nan, len(x)


def resumen(nombre, r, extra=""):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    t, n = tstat(r)
    return f"{nombre:28s} n={n:5d} media={r.mean():+.4f} t={t:+.2f} {extra}"
