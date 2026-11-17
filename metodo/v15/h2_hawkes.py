"""v15 H2: choques endógenos (revierten) frente a exógenos (siguen) con un Hawkes exponencial (PREREGISTRO_V15.md)."""
import sys
import numpy as np, pandas as pd
from scipy.optimize import minimize
from comun import cargar, barajar, resumen, tstat, COSTE
MERC = ["US100", "US500", "US30", "GER40"]

def saltos(X):
    """Minutos con |r1|/sigma1(minuto del día) >= 4; sigma1 de las 20 sesiones previas, ventana ±5 min."""
    lc = np.log(X[:, :, 3]); r = np.diff(lc, axis=1)          # r[:, i] = minuto i+1
    D, n = r.shape; ev = [None] * D
    r2 = r ** 2
    for d in range(20, D):
        v = r2[d - 20:d].mean(0)
        v = pd.Series(v).rolling(11, center=True, min_periods=1).mean().values
        ev[d] = np.flatnonzero(np.abs(r[d]) / np.sqrt(v) >= 4) + 1.0   # tiempo = índice de minuto
    return ev

def nll(p, dias, T):
    mu, a, b = np.exp(p); a = a / (1 + a)   # a = ratio de ramificación en (0,1)
    tot = 0.0
    for t in dias:
        if len(t) == 0: tot -= -mu * T; continue
        A = np.zeros(len(t))
        for i in range(1, len(t)): A[i] = np.exp(-b * (t[i] - t[i - 1])) * (1 + A[i - 1])
        lam = mu + a * b * A
        tot -= np.sum(np.log(lam)) - mu * T - a * np.sum(1 - np.exp(-b * (T - t)))
    return tot

def ajustar(dias, T):
    m0 = sum(len(t) for t in dias) / (len(dias) * T)
    best = None
    for b0 in (0.05, 0.3, 1.0):
        r = minimize(nll, [np.log(m0 * 0.6), 0.0, np.log(b0)], args=(dias, T), method="Nelder-Mead",
                     options=dict(maxiter=600, xatol=1e-4, fatol=1e-3))
        if best is None or r.fun < best.fun: best = r
    mu, a, b = np.exp(best.x); return mu, a / (1 + a), b

def lam_antes(t_ev, t0, mu, a, b):
    t = t_ev[t_ev < t0]
    return mu + a * b * np.sum(np.exp(-b * (t0 - t)))

def tramo(o, h, l, c, i0, lado, ent, dist, n):
    stop = ent - lado * dist
    for j in range(i0, min(i0 + n, len(c))):
        if lado == 1 and l[j] <= stop: return ((stop if j == i0 else min(stop, o[j])) - ent) / dist
        if lado == -1 and h[j] >= stop: return (ent - (stop if j == i0 else max(stop, o[j]))) / dist
    j = min(i0 + n, len(c)) - 1
    return lado * (c[j] - ent) / dist

def simular(sim, F, X, ajustes=None):
    D, n, _ = X.shape; T = float(n)
    ev = saltos(X)
    anios = sorted(set(F.year))
    if ajustes is None:
        ajustes = {}
        for y in anios:
            dias = [ev[d] for d in range(D) if F[d].year == y and ev[d] is not None]
            if len(dias) > 100: ajustes[y] = ajustar(dias, T)
    # sigma 5 min (v3)
    lc = np.log(X[:, :, 3]); r5 = np.diff(lc[:, ::5], axis=1)
    filas = []
    for d in range(20, D):
        y = F[d].year
        if y - 1 not in ajustes or ev[d] is None: continue
        mu, a, b = ajustes[y - 1]
        s5 = r5[d - 20:d].std()
        o, h, l, c = (X[d, :, k] for k in range(4)); libre = 0
        for i in range(5, n - 1):
            if i < 15 or i > n - 46 or i < libre: continue
            rr = lc[d, i] - lc[d, i - 5]; z = abs(rr) / s5
            if z < 4: continue
            t0 = i - 4.0
            lam = lam_antes(ev[d], t0, mu, a, b); eta = 1 - mu / lam
            dist = abs(c[i] - c[i - 5]); ent = o[i + 1]; sg = int(np.sign(rr))
            filas.append(dict(fecha=F[d], sim=sim, hora=i, eta=eta, z=z,
                              contra30=tramo(o, h, l, c, i + 1, -sg, ent, dist, 30),
                              seguir30=tramo(o, h, l, c, i + 1, sg, ent, dist, 30),
                              contra60=tramo(o, h, l, c, i + 1, -sg, ent, dist, 60),
                              seguir60=tramo(o, h, l, c, i + 1, sg, ent, dist, 60),
                              coste=COSTE[sim] * ent / dist))
            libre = i + 31
    return pd.DataFrame(filas), ajustes

def regla(df, umbral=(0.5, 0.5), sal=30, inv=False):
    endo = df.eta >= umbral[1]; exo = df.eta < umbral[0]
    if inv: endo, exo = exo, endo
    d = df[endo | exo].copy()
    d["r"] = np.where(endo[endo | exo], d[f"contra{sal}"], d[f"seguir{sal}"])
    return d

if __name__ == "__main__":
    todo = []; AJ = {}
    for sim in MERC:
        F, X = cargar(sim); df, aj = simular(sim, F, X); todo.append(df); AJ[sim] = aj
        print(sim, "ajustes (mu/min, ramificación, beta):", {y: tuple(round(v, 4) for v in p) for y, p in aj.items()})
    df = pd.concat(todo); df.to_csv("h2_choques.csv", index=False, float_format="%.6g")
    print("choques", len(df), "| proporción endógena", round((df.eta >= 0.5).mean(), 3))
    for nom, kw in [("principal", {}), ("umbral 0,3/0,7", {"umbral": (0.3, 0.7)}), ("salida 60", {"sal": 60}),
                    ("placebo 1 al revés", {"inv": True})]:
        d = regla(df, **kw)
        print(nom, {k: round(v, 3) for k, v in resumen(d, "r").items()})
        if nom == "principal":
            for s, g in d.groupby("sim"): print("   ", s, {k: round(v, 3) for k, v in resumen(g, "r").items() if k in ("ops", "bruto", "neto", "t")})
            for cl, g in [("endógenos contra", d[d.eta >= 0.5]), ("exógenos a favor", d[d.eta < 0.5])]:
                print("   ", cl, {k: round(v, 3) for k, v in resumen(g, "r").items() if k in ("ops", "bruto", "neto", "t")})
            print("   por año neto:", d.assign(n=d.r - d.coste).groupby(d.fecha.dt.year).n.mean().round(3).to_dict())
    # placebo 2: 200 asignaciones aleatorias con la misma proporción por mercado y año
    rng = np.random.default_rng(1); base = df.copy(); base["y"] = base.fecha.dt.year
    endo = (base.eta >= 0.5).values; ms = []
    grupos = base.groupby(["sim", "y"]).indices
    for _ in range(200):
        e2 = np.zeros(len(base), bool)
        for _, ix in grupos.items(): e2[ix] = rng.permutation(endo[ix])
        r = np.where(e2, base.contra30, base.seguir30) - base.coste
        ms.append(pd.Series(r, index=base.index).groupby(base.fecha.values).mean().mean())
    print("placebo 2 aleatorio: p50", round(np.median(ms), 4), "p95", round(np.percentile(ms, 95), 4))
    if "--motor" in sys.argv:
        rs = []
        for s in range(10):
            for sim in MERC:
                F, X = cargar(sim); (Y,) = barajar([X], s)
                d, _ = simular(sim, F, Y, AJ[sim]); rs.append(regla(d).r.values) if len(d) else None
        r = np.concatenate(rs); print("MOTOR barajado: ops", len(r), "bruto", round(r.mean(), 4), "t", round(r.mean() / r.std() * np.sqrt(len(r)), 2))
