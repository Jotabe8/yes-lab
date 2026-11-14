"""Meta-etiquetado del ORB US100 con GEX (ver PREREGISTRO_META_GEX.md)."""
import numpy as np, pandas as pd

D = "metodo/combinar/datos"
g = pd.read_csv(f"{D}/DIX.csv", parse_dates=["date"]).sort_values("date").set_index("date")["gex"]
pct = g.rolling(253).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)  # percentil vs 252 previos
pct_prev = pct.shift(1)  # GEX del día hábil anterior


def unir(fechas):
    idx = pd.DatetimeIndex(fechas)
    return pct_prev.reindex(pct_prev.index.union(idx)).ffill().reindex(idx).values


def tercil(p):
    return np.where(p < 1 / 3, 0, np.where(p > 2 / 3, 2, 1))


def sharpe(x):
    return x.mean() / x.std(ddof=1)


def analiza(fechas, r, coste=None, nombre=""):
    p = unir(fechas)
    ok = ~np.isnan(p)
    f, r, p = np.asarray(fechas)[ok], np.asarray(r)[ok], p[ok]
    t3 = tercil(p)
    w = np.array([1.5, 1.0, 0.5])[t3]
    w = w / w.mean()
    lo, hi = r[t3 == 0], r[t3 == 2]
    dif = lo.mean() - hi.mean()
    tw = dif / np.sqrt(lo.var(ddof=1) / len(lo) + hi.var(ddof=1) / len(hi))
    X = np.column_stack([np.ones_like(p), p])
    b = np.linalg.lstsq(X, r, rcond=None)[0]
    e = r - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    V = XtXi @ (X.T * e**2) @ X @ XtXi
    tb = b[1] / np.sqrt(V[1, 1])
    out = dict(n=len(r), R=r.mean(), sh1=sharpe(r), shw=sharpe(r * w), mejora=sharpe(r * w) - sharpe(r),
               bajo=lo.mean(), medio=r[t3 == 1].mean(), alto=hi.mean(), dif=dif, t_dif=tw,
               pendiente=b[1], t_pend=tb)
    print(f"{nombre}: n {out['n']} R {out['R']:+.3f} | terciles bajo/medio/alto {out['bajo']:+.3f} "
          f"{out['medio']:+.3f} {out['alto']:+.3f} | dif {dif:+.3f} t {tw:+.2f} | pendiente {b[1]:+.3f} "
          f"t {tb:+.2f} | Sharpe 1x {out['sh1']:.4f} con tamaño {out['shw']:.4f} mejora {out['mejora']:+.4f}")
    return out, f, r, p


s = pd.read_csv(f"{D}/orb_us100_2012_2026.csv", parse_dates=["fecha"])
print("=== Réplica Python 2012-2026, neto FTMO ===")
o, f, r, p = analiza(s.fecha, s.neto_ftmo, nombre="TODO")
y = pd.DatetimeIndex(f).year
for a, b in [(2012, 2018), (2019, 2026)]:
    m = (y >= a) & (y <= b)
    analiza(f[m], r[m], nombre=f"{a}-{b}")
analiza(s.fecha, s.bruto, nombre="BRUTO")
analiza(s.fecha, s.neto_ftmo - (s.bruto - s.neto_ftmo), nombre="COSTES x2")

# placebo: desplazamientos circulares de la serie de percentiles
rng = np.random.default_rng(1)
t3 = tercil(p); base = sharpe(r)
mej = []
for _ in range(1000):
    k = rng.integers(60, len(p) - 60)
    pp = np.roll(p, k)
    w = np.array([1.5, 1.0, 0.5])[tercil(pp)]; w = w / w.mean()
    mej.append(sharpe(r * w) - base)
mej = np.array(mej)
print(f"placebo mejora Sharpe p95 {np.percentile(mej, 95):+.4f} | real {o['mejora']:+.4f} | "
      f"p-valor {(mej >= o['mejora']).mean():.3f}")

print("=== Serie real v018 2018-2026 ===")
v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"])
analiza(v.d, v.R, nombre="v018")
