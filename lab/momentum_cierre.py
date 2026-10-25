"""Momentum intradía al cierre en US100, con las reglas de informes/momentum-cierre-preregistro.md.

1. Regresión de la última media hora (22:30-23:00 servidor) sobre el recorrido del día.
2. Estrategia complementaria 22:30 → 22:55 con costes reales y al doble, walk-forward 3 + 1.
3. Extensión del ORB hasta las 22:55 cuando va a favor del recorrido del día.
4. Zona de ruido de Zarattini, Aziz y Barbon (2024) con sus parámetros.
5. EV por cuota en FTMO 2-Step 100K junto al ORB.

Velas M1 de FTMO (US100.cash, bid, columna de spread en centésimas de punto), hora del servidor =
Nueva York + 7 h todo el año (el salto de volumen de las 16:30 no se mueve en las semanas de
desfase de horario de marzo y noviembre). Los datos son del PC de Jorge y no se suben.

Uso:
    python -m lab.momentum_cierre todo --m1 datos/US100_cash_M1_FTMO.csv --orb datos/orb_R_2018_2026.csv
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

APERT, T1700, T2230, T2255, T2259 = 990, 1020, 1350, 1375, 1379
SLIP = 0.2  # puntos por lado
WF = [  # ajuste, prueba
    (("2021-10-01", "2024-09-30"), ("2024-10-01", "2025-09-30")),
    (("2022-10-01", "2025-09-30"), ("2025-10-01", "2026-09-30")),
]


# ---------------------------------------------------------------- datos


def load(path: str, desde: str = "2021-09-14") -> dict:
    df = pd.read_csv(path, parse_dates=["time"])
    df = df[df.time >= desde]
    df["d"] = df.time.dt.normalize()
    df["m"] = df.time.dt.hour * 60 + df.time.dt.minute
    dias = np.array(sorted(df.d.unique()))
    di = np.searchsorted(dias, df.d.values)
    A = {}
    for k, col in [("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("sp", "spread"), ("v", "tick_volume")]:
        a = np.full((len(dias), 1440), np.nan)
        a[di, df.m.values] = df[col].values * (0.01 if k == "sp" else 1)
        A[k] = a
    # ATR14 (media simple del TR) del día anterior, con D1 hechas de M1 del día servidor
    n = np.isfinite(A["o"]).sum(1)
    hi, lo = np.nanmax(A["h"], 1), np.nanmin(A["l"], 1)
    cl = pd.DataFrame(A["c"]).ffill(axis=1).iloc[:, -1].values
    g = pd.DataFrame({"h": hi, "l": lo, "c": cl, "n": n}, index=pd.DatetimeIndex(dias))
    ok = g.n > 300
    gg = g[ok]
    pc = gg.c.shift(1)
    tr = np.maximum(gg.h - gg.l, np.maximum((gg.h - pc).abs(), (gg.l - pc).abs()))
    atr = tr.rolling(14).mean().shift(1).reindex(g.index)
    A["dias"] = pd.DatetimeIndex(dias)
    A["atr"] = atr.values
    A["full"] = ok.values
    return A


def features(A: dict, desde: str = "2021-10-01") -> pd.DataFrame:
    o, c = A["o"], A["c"]
    # C0 = cierre de la vela de las 22:59 del día hábil (completo) anterior
    c2259 = c[:, T2259]
    prev = np.full(len(c2259), np.nan)
    last = np.nan
    for i in range(len(c2259)):
        prev[i] = last
        if A["full"][i] and np.isfinite(c2259[i]):
            last = c2259[i]
    lr = np.diff(np.log(c[:, APERT:T2230]), axis=1)
    f = pd.DataFrame(
        {
            "C0": prev,
            "P1630": o[:, APERT],
            "P1700": o[:, T1700],
            "P2230": o[:, T2230],
            "P2255": o[:, T2255],
            "P2300": c2259,
            "vol": np.nanstd(lr, axis=1),
            "atr": A["atr"],
            "nses": np.isfinite(o[:, APERT:T2259 + 1]).sum(1),
        },
        index=A["dias"],
    )
    f["r_dia"] = f.P2230 / f.C0 - 1
    f["r_1a"] = f.P1700 / f.C0 - 1
    f["r_apert"] = f.P1700 / f.P1630 - 1
    f["r_ult"] = f.P2300 / f.P2230 - 1
    f["r_ult55"] = f.P2255 / f.P2230 - 1
    f["i"] = np.arange(len(f))
    f = f[(f.nses >= 380) & f.atr.notna()].dropna(subset=["C0", "P1630", "P1700", "P2230", "P2255", "P2300"])
    return f[f.index >= desde]


# ---------------------------------------------------------------- estadística


def nw_ols(y: np.ndarray, x: np.ndarray, lags: int = 5) -> tuple[float, float, float]:
    """Pendiente, t de Newey-West y R² de y = a + b x."""
    X = np.column_stack([np.ones_like(x), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    XtXi = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
        S += w * (G + G.T)
    V = XtXi @ S @ XtXi
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    return b[1], b[1] / np.sqrt(V[1, 1]), r2


def tstat(x) -> float:
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else float("nan")


def max_dd(x) -> float:
    eq = np.cumsum(np.nan_to_num(np.asarray(x, float)))
    return float((np.maximum.accumulate(np.concatenate([[0], eq]))[1:] - eq).max())


# ---------------------------------------------------------------- 1. regresión


def regresion(f: pd.DataFrame) -> None:
    print("\n=== 1. Regresión de r_últ (22:30-23:00) ===")
    vc = f.vol.quantile([1 / 3, 2 / 3]).values
    f = f.assign(terc=np.digitize(f.vol, vc))
    grupos = [("Todo", f)] + [(str(y), g) for y, g in f.groupby(f.index.year)] + [
        (f"Vol {n}", f[f.terc == k]) for k, n in enumerate(["baja", "media", "alta"])
    ]
    print(f"{'grupo':<10}{'n':>5} | {'b r_día':>8}{'t':>6}{'R²%':>6}{'acierto':>8} | {'b r_1ª':>8}{'t':>6} | {'b r_apert':>9}{'t':>6}")
    for nm, g in grupos:
        y = g.r_ult.values * 1e4
        out = []
        for col in ["r_dia", "r_1a", "r_apert"]:
            b, t, r2 = nw_ols(y, g[col].values * 1e4)
            out.append((b, t, r2))
        hit = (np.sign(g.r_dia) == np.sign(g.r_ult)).mean() * 100
        print(f"{nm:<10}{len(g):>5} | {out[0][0]:>8.4f}{out[0][1]:>6.1f}{out[0][2]*100:>6.2f}{hit:>7.1f}% | {out[1][0]:>8.4f}{out[1][1]:>6.1f} | {out[2][0]:>9.4f}{out[2][1]:>6.1f}")


# ---------------------------------------------------------------- 2. estrategia complementaria


def trade(A: dict, i: int, s: int, t0: int, t1: int, R: float, k: float = 1.0, exit_close: bool = False) -> float:
    """R de una operación de dirección s abierta en la apertura de t0 y cerrada en t1.

    exit_close: sale al cierre de la vela t1 (si no, a la apertura de t1). k multiplica los costes.
    Stop de protección a 1 R comprobado con máximos y mínimos M1 (ask = bid + spread)."""
    if s == 0:
        return np.nan
    o, h, l, c, sp = A["o"][i], A["h"][i], A["l"][i], A["c"][i], np.nan_to_num(A["sp"][i]) * k
    slip = SLIP * k
    ent = o[t0] + sp[t0] + slip if s > 0 else o[t0] - slip
    stop = ent - s * R
    last = t1 + 1 if exit_close else t1
    for m in range(t0, last):
        if not np.isfinite(o[m]):
            continue
        if s > 0 and l[m] <= stop:
            px = min(o[m], stop) if m > t0 else stop
            return (px - slip - ent) / R
        if s < 0 and h[m] + sp[m] >= stop:
            px = max(o[m] + sp[m], stop) if m > t0 else stop
            return (ent - px - slip) / R
    if exit_close:
        px = c[t1]
        spx = sp[t1]
    else:
        px = o[t1]
        spx = sp[t1]
    return s * ((px - slip if s > 0 else px + spx + slip) - ent) / R


def complementaria_r(A: dict, f: pd.DataFrame, senal: str, k: float, exit_close: bool = False) -> pd.Series:
    out = {}
    for d, x in f.iterrows():
        s = int(np.sign(x[senal]))
        out[d] = trade(A, int(x.i), s, T2230, T2259 if exit_close else T2255, x.atr * 0.15, k, exit_close)
    return pd.Series(out)


def complementaria(A: dict, f: pd.DataFrame) -> dict:
    print("\n=== 2. Estrategia complementaria (22:30 → 22:55, stop 1 R = 15 % ATR) ===")
    sp = pd.DataFrame(A["sp"][f.i.values][:, T2230:T2259 + 3], index=f.index, columns=range(T2230, T2259 + 3))
    print("Spread (puntos) por minuto, mediana / P90:")
    print("  " + " ".join(f"{m//60}:{m%60:02d} {sp[m].median():.1f}/{sp[m].quantile(.9):.1f}" for m in [1350, 1360, 1370, 1375, 1379, 1380, 1381]))
    print(f"  precio medio {f.P2230.mean():.0f} | 1 R medio {(f.atr*0.15).mean():.1f} puntos | |r_últ| medio {(f.r_ult.abs()*f.P2230).mean():.1f} puntos")
    S = {}
    for senal in ["r_dia", "r_1a"]:
        for k in [0.0, 1.0, 2.0]:
            S[(senal, k)] = complementaria_r(A, f, senal, k)
    S[("r_dia_2259", 1.0)] = complementaria_r(A, f, "r_dia", 1.0, exit_close=True)
    S[("r_dia_2259", 2.0)] = complementaria_r(A, f, "r_dia", 2.0, exit_close=True)

    def fila(nm, r):
        r = r.dropna()
        return f"{nm:<28} n {len(r):>4} | R/op {r.mean():+.4f} (t {tstat(r):+.1f}) | acierto {(r>0).mean()*100:.0f}% | DD {max_dd(r):.1f} R"

    for (senal, k), r in S.items():
        print(fila(f"{senal} costes x{k:g}", r))
    print("Por año (r_día, costes x1 / x2):")
    a, b = S[("r_dia", 1.0)], S[("r_dia", 2.0)]
    for y in sorted(set(a.index.year)):
        print(f"  {y}: {a[a.index.year==y].mean():+.4f} / {b[b.index.year==y].mean():+.4f}  (n {(a.index.year==y).sum()})")

    print("\nWalk-forward 3 + 1 (elige en ajuste entre señal × filtro de volatilidad, costes x1):")
    for (fa, fb), (pa, pb) in WF:
        fit, test = f.loc[fa:fb], f.loc[pa:pb]
        best = None
        for senal in ["r_dia", "r_1a"]:
            for filt, q in [("ninguno", 0.0), ("tercil alto", 2 / 3), ("mitad alta", 0.5)]:
                cut = fit.vol.quantile(q) if q > 0 else -np.inf
                rf = S[(senal, 1.0)].loc[fit.index][fit.vol >= cut].mean()
                if best is None or rf > best[0]:
                    best = (rf, senal, filt, cut)
        rf, senal, filt, cut = best
        sel = test.index[test.vol >= cut]
        r1, r2 = S[(senal, 1.0)].loc[sel].dropna(), S[(senal, 2.0)].loc[sel].dropna()
        b1, b2 = S[("r_dia", 1.0)].loc[test.index].dropna(), S[("r_dia", 2.0)].loc[test.index].dropna()
        print(f"  prueba {pa[:7]}→{pb[:7]}: elegida {senal}, filtro {filt} (ajuste {rf:+.4f}) → x1 {r1.mean():+.4f} (t {tstat(r1):+.1f}, n {len(r1)}), x2 {r2.mean():+.4f}"
              f" | sin ajuste r_día: x1 {b1.mean():+.4f} (t {tstat(b1):+.1f}), x2 {b2.mean():+.4f}")
    oos = f.loc[WF[0][1][0]:WF[1][1][1]].index
    r = S[("r_dia", 1.0)].loc[oos].dropna()
    print(f"  dos ventanas juntas, sin ajuste, x1: {r.mean():+.4f} (t {tstat(r):+.1f})")
    return S


# ---------------------------------------------------------------- 3. extensión del ORB


def orb_day(A: dict, i: int, end: int, k: float = 1.0, orm=10, body=10, atrpct=15, act=3.0, dist=1.0):
    """Copia de walkforward/sim.py:sim_day con salida al cierre de la vela end-1 y costes x k."""
    s = APERT
    m = np.arange(s, end)
    o, h, l, c = (A[x][i, s:end] for x in "ohlc")
    sp = A["sp"][i, s:end] * k
    ok = np.isfinite(o)
    m, o, h, l, c, sp = m[ok], o[ok], h[ok], l[ok], c[ok], sp[ok]
    rng = (m >= s) & (m < s + orm)
    if rng.sum() < max(1, orm - 2):
        return None
    ri = np.where(rng)[0]
    hi, lo = h[ri].max(), l[ri].min()
    r = hi - lo
    if r <= 0:
        return None
    b = c[ri[-1]] - o[ri[0]]
    if abs(b) < r * body / 100:
        return None
    dr = 1 if b > 0 else -1
    ei = np.where((m >= s + orm) & (m <= s + orm + 5))[0]
    if len(ei) == 0:
        return None
    kk = ei[0]
    R = A["atr"][i] * atrpct / 100
    if dr == 1:
        ent = o[kk] + sp[kk]
        fav = h[kk:] - ent
        adv = l[kk:]
    else:
        ent = o[kk]
        fav = ent - (l[kk:] + sp[kk:])
        adv = h[kk:] + sp[kk:]
    cm = np.concatenate([[0], np.maximum.accumulate(fav)[:-1]])
    stopoff = np.where(cm >= act * R, cm - dist * R, -R)
    stop = ent + dr * stopoff
    hit = (adv <= stop) if dr == 1 else (adv >= stop)
    oo = o[kk:] if dr == 1 else o[kk:] + sp[kk:]
    if hit.any():
        j = np.argmax(hit)
        px = stop[j] if j == 0 else (min(oo[j], stop[j]) if dr == 1 else max(oo[j], stop[j]))
        abierta = False
    else:
        px = c[-1] if dr == 1 else c[-1] + sp[-1]
        abierta = True
    return dr, dr * (px - ent) / R, abierta


def extension(A: dict, f: pd.DataFrame) -> pd.DataFrame:
    print("\n=== 3. Extensión del ORB hasta las 22:55 ===")
    rows = []
    for d, x in f.iterrows():
        i = int(x.i)
        a = orb_day(A, i, T2230)
        if a is None:
            continue
        dr, r30, abierta = a
        row = dict(d=d, dr=dr, abierta=abierta, fav=dr == np.sign(x.r_dia))
        for k in [1.0, 2.0]:
            base = orb_day(A, i, T2230, k)[1]
            larga = orb_day(A, i, T2255, k)[1]
            row[f"base{k:g}"] = base
            row[f"control{k:g}"] = larga
            row[f"ext{k:g}"] = larga if row["fav"] else base
        rows.append(row)
    E = pd.DataFrame(rows).set_index("d")
    ab = E[E.abierta]
    print(f"Operaciones ORB {len(E)} | abiertas a las 22:30 {len(ab)} ({len(ab)/len(E)*100:.0f}%), a favor del día {ab.fav.mean()*100:.0f}% de ellas")
    for nm, g in [("Todo", E), ("Prueba 1 (2024-10→2025-09)", E.loc["2024-10-01":"2025-09-30"]), ("Prueba 2 (2025-10→2026-09)", E.loc["2025-10-01":"2026-09-30"])]:
        for k in [1.0, 2.0]:
            dif = g[f"ext{k:g}"] - g[f"base{k:g}"]
            dc = g[f"ext{k:g}"] - g[f"control{k:g}"]
            print(f"  {nm:<28} x{k:g}: base {g[f'base{k:g}'].mean():+.4f} | ext {g[f'ext{k:g}'].mean():+.4f} | control {g[f'control{k:g}'].mean():+.4f}"
                  f" | ext−base {dif.mean():+.4f} (t {tstat(dif[dif!=0]):+.1f}, {int((dif!=0).sum())} ops) | ext−control {dc.mean():+.4f}")
    g = ab
    print("  Solo abiertas a las 22:30, 22:30→22:55 (x1): a favor {:+.4f} R (n {}), en contra {:+.4f} R (n {})".format(
        (g.control1 - g.base1)[g.fav].mean(), int(g.fav.sum()), (g.control1 - g.base1)[~g.fav].mean(), int((~g.fav).sum())))
    return E


# ---------------------------------------------------------------- 4. zona de ruido


def zarattini(A: dict, f: pd.DataFrame, k: float, look: int = 14, step: int = 30, hard: float | None = None) -> pd.Series:
    """R diario de la zona de ruido. look, step: días de la media y minutos entre controles (artículo: 14 y 30).

    hard: stop fijo intrabarra a hard R de la entrada (no está en el artículo; solo para la prueba de colas)."""
    o, h, l, c, v, sp = A["o"], A["h"], A["l"], A["c"], np.nan_to_num(A["v"]), np.nan_to_num(A["sp"])
    checks = list(range(APERT + step, T2230 + 1, step))
    mov = np.abs(c[:, [t - 1 for t in checks]] / o[:, [APERT]] - 1)  # movimiento desde la apertura a cada hora de control
    idx = f.i.values
    out = {}
    slip = SLIP * k
    for n, (d, x) in enumerate(f.iterrows()):
        if n < look:
            continue
        i = int(x.i)
        sig = np.nanmean(mov[idx[n - look:n]], axis=0)
        P0, C0 = x.P1630, x.C0
        ub, lb = max(P0, C0) * (1 + sig), min(P0, C0) * (1 - sig)
        tp = (h[i] + l[i] + c[i]) / 3
        R = x.atr * 0.15
        pos, ent, pnl = 0, 0.0, 0.0
        for j, t in enumerate(checks + [T2255]):
            if hard is not None and pos != 0:  # stop fijo entre el control anterior y este
                stp = ent - pos * hard * R
                for m in range(checks[j - 1], t):
                    if not np.isfinite(o[i, m]):
                        continue
                    if pos > 0 and l[i, m] <= stp:
                        pnl += min(o[i, m], stp) - slip - ent
                        pos = 0
                        break
                    if pos < 0 and h[i, m] + sp[i, m] * k >= stp:
                        pnl += ent - max(o[i, m] + sp[i, m] * k, stp) - slip
                        pos = 0
                        break
            if t == T2255:
                break
            q, px = c[i, t - 1], o[i, t]  # se decide con el cierre de la vela anterior y se ejecuta en la apertura
            if not (np.isfinite(px) and np.isfinite(q)):
                continue
            seg = slice(APERT, t)
            w = v[i, seg] if v[i, seg].sum() > 0 else np.isfinite(tp[seg]).astype(float)  # Dukascopy no trae volumen
            vw = np.nansum(tp[seg] * w) / w.sum()
            tgt = pos
            if pos > 0 and q < max(ub[j], vw):
                tgt = 0
            if pos < 0 and q > min(lb[j], vw):
                tgt = 0
            if q > ub[j]:
                tgt = 1
            elif q < lb[j]:
                tgt = -1
            if tgt != pos:
                s_ = sp[i, t] * k
                if pos != 0:
                    pnl += pos * ((px - slip if pos > 0 else px + s_ + slip) - ent)
                if tgt != 0:
                    ent = px + s_ + slip if tgt > 0 else px - slip
                pos = tgt
        if pos != 0:
            px = o[i, T2255]
            s_ = sp[i, T2255] * k
            pnl += pos * ((px - slip if pos > 0 else px + s_ + slip) - ent)
        out[d] = pnl / R
    return pd.Series(out)


def vecindad(A: dict, f: pd.DataFrame) -> None:
    print("\n=== 4b. Zona de ruido: vecindad de parámetros y stop fijo (no se elige nada, solo robustez; costes x2) ===")
    oos = slice(WF[0][1][0], WF[1][1][1])
    for look in [10, 14, 20]:
        for step in [15, 30, 60]:
            z = zarattini(A, f, 2.0, look, step)
            print(f"  look {look:>2} step {step:>2}: todo {z.mean():+.4f} (t {tstat(z):+.1f}) | 2024-10→2026-09 {z.loc[oos].mean():+.4f} (t {tstat(z.loc[oos]):+.1f})")
    for hard in [1.0, 1.5, 2.0]:
        z = zarattini(A, f, 2.0, hard=hard)
        print(f"  stop fijo {hard:g} R: todo {z.mean():+.4f} (t {tstat(z):+.1f}) | 2024-10→2026-09 {z.loc[oos].mean():+.4f} | peor día {z.min():+.2f} R | P1 {z.quantile(.01):+.2f} R")


def ruido(A: dict, f: pd.DataFrame, E: pd.DataFrame) -> dict:
    print("\n=== 4. Zona de ruido (Zarattini, Aziz y Barbon), sin ajuste ===")
    Z = {k: zarattini(A, f, k) for k in [0.0, 1.0, 2.0]}
    for k, z in Z.items():
        act = z[z != 0]
        print(f"  costes x{k:g}: R/día {z.mean():+.4f} (t {tstat(z):+.1f}) | días con operación {len(act)} de {len(z)} | R/día activo {act.mean():+.4f} | DD {max_dd(z):.1f} R")
    z = Z[1.0]
    print(f"  Peor día {z.min():+.2f} R | P1 {z.quantile(.01):+.2f} R | días < −1 R {(z < -1).sum()} | < −1,5 R {(z < -1.5).sum()} | mejor {z.max():+.2f} R")
    for nm, (a, b) in [("Prueba 1", WF[0][1]), ("Prueba 2", WF[1][1])]:
        print(f"  {nm} {a[:7]}→{b[:7]}: x1 {Z[1.0].loc[a:b].mean():+.4f} (t {tstat(Z[1.0].loc[a:b]):+.1f}) | x2 {Z[2.0].loc[a:b].mean():+.4f}")
    print("  Por año x1: " + " ".join(f"{y}:{g.mean():+.3f}" for y, g in Z[1.0].groupby(Z[1.0].index.year)))
    j = pd.concat([Z[1.0], E.base1], axis=1).dropna()
    print(f"  Correlación diaria con el ORB: {j.corr().iloc[0,1]:.2f}")
    oos = pd.concat([Z[1.0].loc[a:b] for a, b in [WF[0][1], WF[1][1]]])
    print(f"  Dos ventanas fuera de muestra juntas x1: {oos.mean():+.4f} (t {tstat(oos):+.1f})")
    return Z


# ---------------------------------------------------------------- combinación y EV


def combinacion(S: dict, E: pd.DataFrame, Z: dict) -> None:
    print("\n=== Combinación con el ORB (misma fracción de riesgo, costes x2, 2021-10 → 2026-09) ===")
    orb = E.base2
    for nm, s in [("Complementaria r_día", S[("r_dia", 2.0)]), ("Zona de ruido", Z[2.0])]:
        j = pd.concat([orb.rename("orb"), s.rename("x")], axis=1).fillna(0)
        cmb = j.orb + j.x
        print(f"  {nm:<22} suma {j.x.sum():+.1f} R | DD ORB {max_dd(j.orb):.1f} R → combinado {max_dd(cmb):.1f} R (sube {max_dd(cmb)-max_dd(j.orb):+.1f}) | corr {j.corr().iloc[0,1]:+.2f}")


def ev_cuota(orb_path: str, S: dict, Z: dict, N: int = 10000, seed: int = 7) -> None:
    """Simulador de cartera/anio_100k.py (modo Swing) con el R diario del ORB solo y con cada candidata."""
    print("\n=== 5. EV por cuota, FTMO 2-Step 100K (cuota 439 €, reto 2 %, fondeada 1,5 %, +0,05 R de coste/op) ===")
    orb = pd.read_csv(orb_path, index_col=0, parse_dates=True).iloc[:, 0]
    comp = S[("r_dia", 1.0)].dropna()
    orb = orb.loc[comp.index.min():comp.index.max()]
    cal = pd.bdate_range(comp.index.min(), comp.index.max())
    HC, FEE, SIZE, EUR, RC, RF = 0.05, 439.0, 100000, 1.12, 2.0, 1.5

    def year(X):
        rng = np.random.default_rng(seed)
        block, days = 20, 252
        st = rng.integers(0, len(X) - block, (N, days // block + 1))
        idx = (st[:, :, None] + np.arange(block)).reshape(N, -1)[:, :days]
        r = X[idx]
        has = r != 0
        bal = np.zeros(N); stg = np.zeros(N, int); tdays = np.zeros(N); since = np.zeros(N)
        refunded = np.zeros(N, bool); fees = np.ones(N); pay = np.zeros(N)
        for t in range(days):
            fund = stg == 2
            risk = np.where(fund, RF, RC)
            pnl = r[:, t] * risk
            bal += pnl
            tdays += has[:, t]
            fail = (bal <= -10) | (pnl <= -5)
            p1 = (stg == 0) & ~fail & (bal >= 10) & (tdays >= 4)
            p2 = (stg == 1) & ~fail & (bal >= 5) & (tdays >= 4)
            since = np.where(fund, since + 1, 0)
            can = fund & ~fail & (since >= 10) & (bal > 0)
            pay += np.where(can, bal / 100 * SIZE * 0.8 / EUR, 0) + np.where(can & ~refunded, FEE, 0)
            refunded |= can
            since = np.where(can, 0, since)
            fees += fail
            stg = np.where(fail, 0, np.where(p1, 1, np.where(p2, 2, stg)))
            reset = fail | p1 | p2 | can
            bal = np.where(reset, 0, bal); tdays = np.where(fail | p1 | p2, 0, tdays); refunded = np.where(fail, False, refunded)
        net = pay - fees * FEE
        return net.mean(), np.median(net), np.percentile(net, 10), (net > 0).mean() * 100, fees.mean()

    def serie(s, cap=None):
        s = s.reindex(cal)
        x = np.where(s.notna() & (s != 0), s - HC, 0.0)
        return np.maximum(x, cap) if cap is not None else x

    x_orb = serie(orb, -1.5)  # como anio_100k.py: deslizamiento máximo 1,5 R en el stop del ORB
    x_cmp, z1, z2 = serie(comp, -1.5), serie(Z[1.0]), serie(Z[2.0])
    for nm, X in [("ORB solo", x_orb), ("ORB + complementaria", x_orb + x_cmp), ("Complementaria sola", x_cmp),
                  ("ORB + zona de ruido x1", x_orb + z1), ("ORB + zona de ruido x2", x_orb + z2), ("Zona de ruido sola x1", z1),
                  ("ORB x1,25 (control)", 1.25 * x_orb), ("ORB x1,5 (control)", 1.5 * x_orb),
                  ("ORB + ruido x2 a 0,25", x_orb + 0.25 * z2), ("ORB + ruido x2 a 0,5", x_orb + 0.5 * z2), ("ORB + ruido x1 a 0,5", x_orb + 0.5 * z1)]:
        m, med, p10, pp, fe = year(X)
        print(f"  {nm:<22} neto medio {m:+8,.0f} € | mediana {med:+8,.0f} € | P10 {p10:+8,.0f} € | P(neto>0) {pp:.0f}% | cuotas {fe:.1f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prueba", choices=["todo"])
    ap.add_argument("--m1", default="datos/US100_cash_M1_FTMO.csv")
    ap.add_argument("--orb", default="datos/orb_R_2018_2026.csv")
    ap.add_argument("--duka", default="datos/US100_M1_DUKA_2018_2022.csv", help="vacío para no correrlo")
    a = ap.parse_args()
    A = load(a.m1)
    f = features(A)
    print(f"Días {len(f)}: {f.index.min().date()} → {f.index.max().date()}")
    regresion(f)
    S = complementaria(A, f)
    E = extension(A, f)
    Z = ruido(A, f, E)
    vecindad(A, f)
    combinacion(S, E, Z)
    ev_cuota(a.orb, S, Z)
    if a.duka:
        print("\n=== Dukascopy 2018-01 → 2021-09 (fuera del periodo FTMO, solo informativo) ===")
        B = load(a.duka, desde="2018-01-01")
        g = features(B, desde="2018-01-01")
        g = g[g.index < "2021-10-01"]
        for k in [1.0, 2.0]:
            r = complementaria_r(B, g, "r_dia", k).dropna()
            z = zarattini(B, g, k)
            print(f"  costes x{k:g}: complementaria {r.mean():+.4f} R (t {tstat(r):+.1f}, n {len(r)}) | zona de ruido {z.mean():+.4f} R/día (t {tstat(z):+.1f}, n {len(z)})")
        z = zarattini(B, g, 1.0)
        print("  Zona de ruido por año x1: " + " ".join(f"{y}:{x.mean():+.3f}" for y, x in z.groupby(z.index.year)))


if __name__ == "__main__":
    main()
