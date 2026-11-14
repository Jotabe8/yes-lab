"""Análisis preregistrado de la zona de ruido (metodo/v8/PREREGISTRO_ZONA_RUIDO.md)."""
import glob, sys
import numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "metodo/v8/zona_ruido"
ORB = sys.argv[2] if len(sys.argv) > 2 else "/mnt/project-files/donde-operar/serie_v018_be.csv"
COSTE = {"GER40": 0.000052, "UK100": 0.000079, "EU50": 0.000268}

def leer(m, tipo):
    fs = sorted(glob.glob(f"{D}/{m}_{tipo}_*.csv"))
    return pd.concat([pd.read_csv(f, parse_dates=["fecha"]) for f in fs]).drop_duplicates("fecha").set_index("fecha").sort_index() if fs else None

def st(x):
    x = x.dropna(); return f"{x.mean():+.4f} R t {x.mean()/x.std(ddof=1)*np.sqrt(len(x)):+5.2f} (n {len(x)})" if len(x) > 2 else "n<3"

R = {}
for m, c in COSTE.items():
    d = leer(m, "dias")
    if d is None: print(m, "sin datos"); continue
    d = d[d.sd14 > 0]
    out = {}
    for v in ["base", "contra", "hora15"]:
        out[f"{v}_bruto"] = d[f"r_{v}"] / d.sd14
        out[f"{v}_neto"] = (d[f"r_{v}"] - c * d[f"n_{v}"]) / d.sd14
        out[f"{v}_x2"] = (d[f"r_{v}"] - 2 * c * d[f"n_{v}"]) / d.sd14
    out = pd.DataFrame(out); R[m] = out
    anos = (d.index[-1] - d.index[0]).days / 365.25
    print(f"\n== {m} {d.index[0].date()} → {d.index[-1].date()}  días con op {int((d.n_base>0).sum())} ({(d.n_base>0).sum()/anos:.0f}/año), ops {int(d.n_base.sum())}, coste/op en R ≈ {(c/d.sd14).median():.3f}")
    for v in ["base", "contra", "hora15"]:
        print(f"  {v:7s} bruto {st(out[v+'_bruto'])} | neto {st(out[v+'_neto'])} | x2 {st(out[v+'_x2'])}")
    print("  base neto por año:", " ".join(f"{y}:{v:+.3f}" for y, v in out.base_neto.groupby(out.index.year).mean().items()))

if "GER40" in R and "UK100" in R:
    cart = pd.concat([R["GER40"], R["UK100"]], axis=1, keys=["G", "U"]).dropna()
    C = {k: (cart["G"][k] + cart["U"][k]) / 2 for k in ["base_bruto", "base_neto", "base_x2", "contra_neto", "hora15_neto"]}
    C = pd.DataFrame(C)
    mitad = C.index[0] + (C.index[-1] - C.index[0]) / 2
    print("\n== CARTERA GER40+UK100 (media de R diarios)")
    for k in C: print(f"  {k:12s} {st(C[k])}")
    print("  1ª mitad neto", st(C.base_neto[C.index < mitad]), "| 2ª mitad", st(C.base_neto[C.index >= mitad]))
    print("  2023-26 neto", st(C.base_neto[C.index >= "2023-01-01"]))
    print("  por año:", " ".join(f"{y}:{v:+.3f}" for y, v in C.base_neto.groupby(C.index.year).mean().items()))
    # placebo: signo aleatorio por operación
    rng = np.random.default_rng(7); real = C.base_bruto.sum(); pl = []
    og = leer("GER40", "ops"); ou = leer("UK100", "ops")
    dg = leer("GER40", "dias").sd14; du = leer("UK100", "dias").sd14
    og = og.reset_index(); ou = ou.reset_index()
    og["r"] = og.ret.values / dg.reindex(og.fecha).values; ou["r"] = ou.ret.values / du.reindex(ou.fecha).values
    todo = np.r_[og.r.dropna().values, ou.r.dropna().values] / 2
    for _ in range(500): pl.append((todo * rng.choice([-1, 1], len(todo))).sum())
    print(f"  placebo signo (bruto, suma R): real {real:.1f} | p95 {np.percentile(pl,95):.1f} | p50 {np.percentile(pl,50):.1f}")
    # DD a vol 15 %
    x = C.base_neto; esc = 0.15 / (x.std() * np.sqrt(252)); eq = (x * esc).cumsum()
    print(f"  a vol 15 %: anual {x.mean()*252*esc*100:.1f} % (en unidades de R), DD {(eq.cummax()-eq).max()*100:.1f} %")
    try:
        orb = pd.read_csv(ORB, parse_dates=["d"]).set_index("d").R
        j = pd.concat([C.base_neto, orb], axis=1, sort=True).dropna()
        print(f"  corr con ORB v018 (días comunes {len(j)}): {j.corr().iloc[0,1]:.3f}")
    except Exception as e: print("  sin ORB", e)
