"""v15 H1: valor relativo intradía entre índices US con beta de Kalman (PREREGISTRO_V15.md)."""
import sys
import numpy as np, pandas as pd
from comun import cargar, barajar, resumen, tstat, COSTE
PARES = [("US500", "US100"), ("US500", "US30"), ("US100", "US30")]
K0, K1, KX = 5, 65, 76          # velas de 5 min: 10:00, 15:00, 15:55

def velas5(X):
    c = X[:, 4::5, 3]            # cierre de cada vela de 5 min (78)
    return np.diff(np.log(c), axis=1)   # r[:, j] = vela j+1 (9:35-9:40 es j=0)

def simular(F, XA, XB, a, b, z_ent=2.0, con_obj=True):
    rA, rB = velas5(XA), velas5(XB)          # D x 77
    D, n = rA.shape
    filas = []; E = np.full((D, n), np.nan); Sday = np.full((D, n), np.nan)
    # arranque MCO 20 sesiones
    beta = np.sum(rA[:20] * rB[:20]) / np.sum(rB[:20] ** 2)
    P = 1e-2
    for d in range(D):
        if d >= 20:
            e_prev = E[d - 20:d].ravel(); e_prev = e_prev[~np.isnan(e_prev)]
            R = e_prev.var(); q = 1e-4 * R / rB[d - 20:d].var(); sig = np.sqrt(R)
        else:
            R = (rA[d] - beta * rB[d]).var(); q = 1e-4 * R / rB[d].var(); sig = None
        betas = np.empty(n)
        for k in range(n):
            P += q; betas[k] = beta
            e = rA[d, k] - beta * rB[d, k]; E[d, k] = e
            S_ = P * rB[d, k] ** 2 + R; K = P * rB[d, k] / S_
            beta += K * e; P = (1 - K * rB[d, k]) * P
        S = np.cumsum(E[d]); Sday[d] = S
        if sig is None: continue
        kk = np.arange(1, n + 1)
        z = S / (sig * np.sqrt(kk))
        # índices: S[j] es el acumulado al cierre de la vela j+1 -> vela k = j+1
        cand = [j for j in range(K0 - 1, K1) if abs(z[j]) >= z_ent]
        if not cand: continue
        j = cand[0]; s = np.sign(S[j]); S0 = S[j]; b0 = betas[j + 1] if j + 1 < n else betas[j]
        T = S0; r = None
        for i in range(j + 1, KX):
            T += rA[d, i] - b0 * rB[d, i]
            if s * T >= 2 * abs(S0): r = -1 - (s * T - 2 * abs(S0)) / abs(S0); break
            if con_obj and s * T <= 0: r = (abs(S0) - s * T) / abs(S0); break
        if r is None: r = (abs(S0) - s * T) / abs(S0)
        filas.append(dict(fecha=F[d], par=f"{a}/{b}", k=j + 1, S0=S0, beta=b0, r=r,
                          coste=(COSTE[a] + abs(b0) * COSTE[b]) / abs(S0)))
    return pd.DataFrame(filas), Sday, E

def placebo_dia_anterior(F, XA, XB, ops, Sday, a, b):
    rA, rB = velas5(XA), velas5(XB); n = rA.shape[1]
    idx = {f: i for i, f in enumerate(F)}; filas = []
    for _, o in ops.iterrows():
        d = idx[o.fecha] - 1; j = o.k - 1
        if d < 0: continue
        s = np.sign(Sday[d, j]) or 1.0; S0 = abs(o.S0) * s; T = S0; r = None
        for i in range(j + 1, KX):
            T += rA[d, i] - o.beta * rB[d, i]
            if s * T >= 2 * abs(S0): r = -1 - (s * T - 2 * abs(S0)) / abs(S0); break
            if s * T <= 0: r = (abs(S0) - s * T) / abs(S0); break
        if r is None: r = (abs(S0) - s * T) / abs(S0)
        filas.append(dict(fecha=o.fecha, par=o.par, r=r, coste=o.coste))
    return pd.DataFrame(filas)

def alinear(a, b):
    Fa, Xa = cargar(a); Fb, Xb = cargar(b)
    com = Fa.intersection(Fb)
    ia = Fa.get_indexer(com); ib = Fb.get_indexer(com)
    return com, Xa[ia], Xb[ib]

if __name__ == "__main__":
    datos = {p: alinear(*p) for p in PARES}
    res = {}
    for nombre, kw in [("principal z2", {}), ("z2,5", {"z_ent": 2.5}), ("sin objetivo", {"con_obj": False})]:
        ops = []; plac = []
        for (a, b), (F, XA, XB) in datos.items():
            o, Sd, _ = simular(F, XA, XB, a, b, **kw); ops.append(o)
            if nombre == "principal z2": plac.append(placebo_dia_anterior(F, XA, XB, o, Sd, a, b))
        ops = pd.concat(ops); res[nombre] = ops
        print(nombre, {k: round(v, 3) for k, v in resumen(ops, "r").items()})
        for p, g in ops.groupby("par"):
            print("   ", p, {k: round(v, 3) for k, v in resumen(g, "r").items() if k in ("ops", "bruto", "neto", "t", "coste")})
        if nombre == "principal z2":
            pl1 = ops.assign(r=-ops.r)
            print("  placebo 1 seguir", {k: round(v, 3) for k, v in resumen(pl1, "r").items() if k in ("bruto", "neto", "t")})
            pl2 = pd.concat(plac)
            print("  placebo 2 día anterior", {k: round(v, 3) for k, v in resumen(pl2, "r").items() if k in ("ops", "bruto", "neto", "t")})
            print("  por año neto:", ops.assign(n=ops.r - ops.coste).groupby(ops.fecha.dt.year).n.mean().round(3).to_dict())
            print("  coste R mediana", round(ops.coste.median(), 3), "| |S0| mediana pb", round(ops.S0.abs().median() * 1e4, 1))
    ops = res["principal z2"]; ops.to_csv("h1_ops.csv", index=False, float_format="%.6g")
    if "--motor" in sys.argv:
        rs = []
        for s in range(10):
            for (a, b), (F, XA, XB) in datos.items():
                YA, YB = barajar([XA, XB], s)
                o, _, _ = simular(F, YA, YB, a, b); rs.append(o.r.values)
        r = np.concatenate(rs); print("MOTOR barajado: ops", len(r), "bruto", round(r.mean(), 4), "t", round(r.mean() / r.std() * np.sqrt(len(r)), 2))
