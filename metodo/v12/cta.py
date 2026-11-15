"""v12 flujo forzado CTA. Reglas en PREREGISTRO_CTA.md. Uso: python cta.py"""
import numpy as np, pandas as pd, os
D = os.path.join(os.path.dirname(__file__), "..", "v9", "datos")
IND, REP = ["US500", "US100"], ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
COSTE = {"US500": .8, "US100": .8, "EURUSD": .8, "GBPUSD": .8, "USDJPY": .8, "XAUUSD": 1.2}
LS = [21, 63, 126, 252]
VENT = {"W1": {"ind": (150, 539), "fx": (60, 599)}, "W2": {"ind": (480, 539), "fx": (540, 599)}}
rng = np.random.default_rng(12)

def diario(s):
    g = pd.concat([pd.read_csv(f"{D}/{s}_{y}_diario.csv") for y in (2011, 2019)])
    g = g.drop_duplicates("dia", keep="last").sort_values("dia")
    g["dia"] = pd.to_datetime(g.dia); g = g[(g.dia.dt.dayofweek < 5) & (g.n > 300)]
    return g.set_index("dia").c

def intradia(s):
    fs, xs = [], []
    for y in (2011, 2019):
        z = np.load(f"{D}/{s}_{y}_m1.npz"); fs.append(z["fechas"]); xs.append(z["x"])
    f = np.concatenate(fs); x = np.concatenate(xs)
    _, i = np.unique(f[::-1], return_index=True); i = len(f) - 1 - i  # última aparición
    i = np.sort(i); return pd.to_datetime(f[i]), x[i]

def eventos(s, w):
    c = diario(s)
    S = sum(np.sign(c - c.shift(L)) for L in LS) / len(LS)
    F = S.diff(); r_dia = np.log(c).diff()
    ev = F[(F != 0) & F.notna() & S.shift(LS[-1]).notna()]
    fe, x = intradia(s); k0, k1 = VENT[w]["ind" if s in IND else "fx"]
    filas = []
    for d, f in ev.items():
        j = np.searchsorted(fe.values, np.datetime64(d) + np.timedelta64(1, "D"))
        if j >= len(fe) or (fe[j] - d).days > 4: continue
        o, cl = x[j, k0, 0], x[j, k1, 3]
        if np.isnan(o) or np.isnan(cl): continue
        r = (cl / o - 1) * 1e4
        filas.append((fe[j], s, np.sign(f), r, np.sign(r_dia.loc[d]), COSTE[s]))
    return pd.DataFrame(filas, columns=["fecha", "s", "d", "r", "mom", "coste"])

def t(v): v = np.asarray(v); return v.mean() / v.std(ddof=1) * np.sqrt(len(v)) if len(v) > 2 else np.nan

def cartera(e, col_d="d", k=1.0):
    e = e.assign(net=e[col_d] * e.r - k * e.coste)
    return e.groupby("fecha").net.mean()

for w in VENT:
    print(f"\n===== {w} =====")
    for grupo, lst in (("PRINCIPAL", IND), ("REPLICA", REP)):
        e = pd.concat([eventos(s, w) for s in lst])
        for s in lst:
            es = e[e.s == s]; yrs = (es.fecha.max() - es.fecha.min()).days / 365.25
            print(f"  {s}: {len(es)} eventos, {len(es)/yrs:.1f}/año, bruto {np.mean(es.d*es.r):+.2f} pb, sigma {es.r.std():.1f}")
        p = cartera(e); p0 = cartera(e, k=0); p2 = cartera(e, k=2)
        mitad = p[p.index >= "2019-01-01"]
        clon = cartera(e, "mom"); dif = (p - clon).dropna()
        sims = []
        for _ in range(2000):
            ee = e.assign(d=rng.choice([-1, 1], len(e))); sims.append(cartera(ee, k=0).mean())
        p95 = np.percentile(sims, 95)
        print(f"  {grupo}: días {len(p)}, bruto {p0.mean():+.2f} pb, neto {p.mean():+.2f} pb t {t(p):.2f}; "
              f"2019-26 {mitad.mean():+.2f} (t {t(mitad):.2f}); coste x2 {p2.mean():+.2f}; "
              f"placebo azar p95 {p95:+.2f} (bruto {'>' if p0.mean() > p95 else '<='}); "
              f"menos clon momentum {dif.mean():+.2f} t {t(dif):.2f}")
        for y, g in p.groupby(p.index.year): print(f"    {y}: {len(g):3d} días {g.mean():+6.2f}", end="")
        print()
