"""v20: H1-H4 del preregistro. Uso: python hipotesis.py [duka|etf|twap] [p1|oos]"""
import sys
import numpy as np, pandas as pd
from comun import cargar_precio, vol_duka, vol_etf, vwap, atr, tstat, resumen, COSTE, MERCADOS, FIN_P1

PESO = sys.argv[1] if len(sys.argv) > 1 else "duka"
TRAMO = sys.argv[2] if len(sys.argv) > 2 else "p1"
RNG = np.random.default_rng(20261123)
INI_P1 = pd.Timestamp("2012-01-01")


def en_tramo(F):
    return (F >= INI_P1) & (F <= FIN_P1) if TRAMO == "p1" else (F > FIN_P1)


def datos(m):
    F, X = cargar_precio(m)
    w = {"duka": vol_duka, "etf": vol_etf}.get(PESO, lambda *_: None)(m, F)
    if PESO != "twap" and w is None:
        return None
    if w is not None:  # solo días con volumen
        ok = np.isfinite(w).sum(1) > 0.5 * X.shape[1]
        F, X, w = F[ok], X[ok], w[ok]
    vw, sg, _ = vwap(X, w)
    return F, X, vw, sg, atr(X)


def recorrer(d, lado, ent_k, stop, salida_k, salir_antes=None):
    """Recorre M1 de ent_k a salida_k con stop (hueco al open). Devuelve (precio, k de salida)."""
    for k in range(ent_k, salida_k):
        o, h, l = d[k, 0], d[k, 1], d[k, 2]
        if lado > 0 and l <= stop:
            return (stop if k == ent_k else min(stop, o)), k
        if lado < 0 and h >= stop:
            return (stop if k == ent_k else max(stop, o)), k
        if salir_antes is not None:
            r = salir_antes(k)
            if r is not None:
                return r, k
    return d[salida_k, 0], salida_k


# ---------------- H1
def h1(m, F, X, vw, sg, a, senal="z", qa=0.8):
    N = X.shape[1]
    C = X[:, -1, 3]; O = X[:, 0, 0]
    z = (C - vw[:, -1]) / a if senal == "z" else (C - O) / a
    s = pd.Series(z)
    hi = s.rolling(250, min_periods=100).quantile(qa).shift(1).values
    lo = s.rolling(250, min_periods=100).quantile(1 - qa).shift(1).values
    filas = []
    for i in range(len(F) - 1):
        if not (np.isfinite(z[i]) and np.isfinite(hi[i]) and np.isfinite(a[i + 1])):
            continue
        lado = 1 if z[i] > hi[i] else (-1 if z[i] < lo[i] else 0)
        if lado == 0 or (F[i + 1] - F[i]).days > 4:
            continue
        d = X[i + 1]; ent = d[1, 0]; dist = 0.5 * a[i + 1]
        px, _ = recorrer(d, lado, 1, ent - lado * dist, N - 5)
        filas.append((F[i + 1], lado, lado * (px - ent) / dist, COSTE[m] * ent / dist,
                      (d[N - 5, 0] - ent) / dist, z[i], (C[i] - O[i]) / a[i]))
    return pd.DataFrame(filas, columns=["fecha", "lado", "r", "coste", "r_sin_lado", "z", "rend"])


# ---------------- H2 (ORB con stop VWAP)
def orb(m, F, X, vw, a, con_vwap):
    N = X.shape[1]; K0 = 30  # 10:00 (US) / 9:30 (GER40, con sesión 9:00)
    out = []
    for i in range(len(F)):
        d = X[i]
        if not np.isfinite(a[i]):
            out.append(np.nan); continue
        o, c = d[0, 0], d[9, 3]; h, l = d[:10, 1].max(), d[:10, 2].min()
        if h - l <= 0 or abs(c - o) < 0.1 * (h - l):
            out.append(np.nan); continue
        lado = 1 if c > o else -1
        ent = d[10, 0]; dist = 0.15 * a[i]; stop = ent - lado * dist
        fin = 385 if N == 390 else N - 5
        sal = None
        if con_vwap:
            def sal(k):
                if k < K0:
                    return None
                v = vw[i, k]
                if lado > 0 and v > stop and d[k, 3] < v:
                    return d[k + 1, 0]
                if lado < 0 and v < stop and d[k, 3] > v:
                    return d[k + 1, 0]
                return None
        px, _ = recorrer(d, lado, 10, stop, fin, sal)
        out.append(lado * (px - ent) / dist - COSTE[m] * ent / dist)
    return np.array(out)


# ---------------- H3 (bandas ±2σ)
def h3(m, F, X, vw, sg, a, k_ent=2.0, k_stop=3.0):
    N = X.shape[1]; ini, fin_e = (60, 330) if N == 390 else (90, 450); fin = N - 5
    filas = []
    for i in range(len(F)):
        d = X[i]; hechos = set(); k = ini
        while k < fin_e:
            c, v, s_ = d[k, 3], vw[i, k], sg[i, k]
            lado = -1 if c > v + k_ent * s_ else (1 if c < v - k_ent * s_ else 0)
            if lado == 0 or lado in hechos or s_ <= 0:
                k += 1; continue
            hechos.add(lado)
            ent = d[k + 1, 0]; stop = v - lado * k_stop * s_; dist = abs(ent - stop)
            if dist <= 0 or lado * (stop - ent) > 0:
                k += 1; continue

            def obj(j, lado=lado):
                vv = vw[i, j - 1]
                if (lado > 0 and d[j, 1] >= vv) or (lado < 0 and d[j, 2] <= vv):
                    return max(vv, d[j, 0]) if lado > 0 else min(vv, d[j, 0])
                return None
            px, ks = recorrer(d, lado, k + 1, stop, fin, obj)
            filas.append((F[i], lado, lado * (px - ent) / dist, COSTE[m] * ent / dist,
                          (px - ent) / dist, ks - k - 1, lado * (px - ent) / ent - COSTE[m]))
            k = ks + 1
    return pd.DataFrame(filas, columns=["fecha", "lado", "r", "coste", "mov", "dur", "neto_frac"])


# ---------------- H4 (tendencia VWAP)
def h4(m, F, X, vw, marco=1, placebo=False):
    N = X.shape[1]; fin = 385 if N == 390 else N - 5
    idx = np.arange(1, fin, marco)
    r_dia, giros = [], []
    for i in range(len(F)):
        c = X[i, idx, 3]; v = vw[i, idx]; o = X[i, np.minimum(idx + 1, N - 1), 0]
        s = np.sign(c - v); s[s == 0] = 1
        if placebo:
            ng = int((np.diff(s) != 0).sum())
            s = np.ones(len(s)) * RNG.choice([-1, 1])
            if ng:
                pts = RNG.choice(np.arange(1, len(s)), min(ng, len(s) - 1), replace=False)
                fl = np.zeros(len(s)); fl[pts] = 1
                s = s * np.where(np.cumsum(fl) % 2, -1, 1)
        px = np.r_[o, X[i, fin, 0]]
        ret = (s * np.diff(px[: len(s) + 1])).sum() / px[0]
        ng = int((np.diff(s) != 0).sum())
        r_dia.append(ret - (ng + 1) * COSTE[m]); giros.append(ng)
    return np.array(r_dia), np.array(giros)


def placebo_dir(df, n=1000):
    """Media de r con dirección al azar y las mismas salidas (r_sin_lado/mov = movimiento a favor de un largo)."""
    col = "r_sin_lado" if "r_sin_lado" in df else "mov"
    mv = df[col].values
    return np.array([(RNG.choice([-1, 1], len(mv)) * mv).mean() for _ in range(n)])


if __name__ == "__main__":
    print(f"v20 hipótesis — peso {PESO}, tramo {TRAMO}")
    D = {m: datos(m) for m in MERCADOS}
    D = {m: v for m, v in D.items() if v is not None}
    # H1
    print("\nH1 cierre frente al VWAP -> mismo lado al día siguiente (R, 1R = 0,5 ATR)")
    todos, ctl = [], []
    for m, (F, X, vw, sg, a) in D.items():
        g = h1(m, F, X, vw, sg, a); g = g[en_tramo(g.fecha)]; g["m"] = m
        c = h1(m, F, X, vw, sg, a, senal="rend"); c = c[en_tramo(c.fecha)]
        pl = placebo_dir(g)
        print("  " + resumen(m, g.r - g.coste, f"bruto {g.r.mean():+.4f} coste {g.coste.mean():.4f} "
                             f"placebo p95 {np.percentile(pl, 95) - g.coste.mean():+.4f} | control rend {(c.r - c.coste).mean():+.4f}"))
        todos.append(g); ctl.append(c)
    g = pd.concat(todos)
    print("  " + resumen("JUNTOS", g.r - g.coste, f"bruto {g.r.mean():+.4f}"))
    # regresión r_{d+1} (largo) ~ z + rend
    y = g.r_sin_lado.values; A_ = np.c_[np.ones(len(g)), g.z, g.rend]
    b, res, *_ = np.linalg.lstsq(A_, y, rcond=None)
    s2 = ((y - A_ @ b) ** 2).sum() / (len(y) - 3); se = np.sqrt(np.diag(s2 * np.linalg.inv(A_.T @ A_)))
    print(f"  regresión (días con señal): coef z {b[1]:+.4f} t {b[1] / se[1]:+.2f} | coef rend {b[2]:+.4f} t {b[2] / se[2]:+.2f}")
    for qa in (0.7, 0.9):
        gg = pd.concat([h1(m, *v, qa=qa).assign(m=m) for m, v in D.items()]); gg = gg[en_tramo(gg.fecha)]
        print("  " + resumen(f"meseta q{int(qa * 100)}", gg.r - gg.coste))
    # H2
    print("\nH2 ORB con stop dinámico VWAP desde las 10:00 (R neta)")
    for m, (F, X, vw, sg, a) in D.items():
        if m == "GER40":
            continue
        t = en_tramo(F)
        b0 = orb(m, F, X, vw, a, False)[t]; b1 = orb(m, F, X, vw, a, True)[t]
        ok = np.isfinite(b0) & np.isfinite(b1); dlt = b1[ok] - b0[ok]
        sh = lambda r: r.mean() / r.std() * np.sqrt(len(r) / ((F[t][-1] - F[t][0]).days / 365.25))
        print(f"  {m}: ops {ok.sum()} base {b0[ok].mean():+.4f} (t {tstat(b0[ok])[0]:+.2f}) VWAP {b1[ok].mean():+.4f} "
              f"(t {tstat(b1[ok])[0]:+.2f})  Δ {dlt.mean():+.4f} t {tstat(dlt)[0]:+.2f}  Sharpe/año {sh(b0[ok]):.2f} -> {sh(b1[ok]):.2f}")
    # H3
    print("\nH3 bandas ±2σ, vuelta al VWAP (R, 1R = distancia al stop 3σ)")
    todos = []
    for m, (F, X, vw, sg, a) in D.items():
        g = h3(m, F, X, vw, sg, a); g = g[en_tramo(g.fecha)]; g["m"] = m
        pl = placebo_dir(g)
        print("  " + resumen(m, g.r - g.coste, f"bruto {g.r.mean():+.4f} coste {g.coste.mean():.4f} "
                             f"placebo p95 {np.percentile(pl, 95) - g.coste.mean():+.4f} dur med {g.dur.median():.0f} min | neto {g.neto_frac.mean() * 1e4:+.2f} pb/op t {tstat(g.neto_frac)[0]:+.2f}"))
        todos.append(g)
    g = pd.concat(todos); print("  " + resumen("JUNTOS", g.r - g.coste, f"bruto {g.r.mean():+.4f}"))
    # H4
    print("\nH4 tendencia VWAP (rendimiento diario neto, pb = 1e-4)")
    for marco in (1, 5):
        tot = []
        for m, (F, X, vw, sg, a) in D.items():
            t = en_tramo(F)
            r, ng = h4(m, F[t], X[t], vw[t], marco)
            rp = np.array([h4(m, F[t], X[t], vw[t], marco, placebo=True)[0].mean() for _ in range(20)])
            bruto = r + (ng + 1) * COSTE[m]
            print(f"  M{marco} {m}: días {len(r)} neto {r.mean() * 1e4:+.2f} pb t {tstat(r)[0]:+.2f} bruto {bruto.mean() * 1e4:+.2f} pb "
                  f"giros/día {ng.mean():.1f}  placebo neto p95 {np.percentile(rp, 95) * 1e4:+.2f} pb")
            tot.append(r)
        print("  " + resumen(f"M{marco} JUNTOS (fracción)", np.concatenate(tot)))
