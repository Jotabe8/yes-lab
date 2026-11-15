"""v10-bis: H2a y H2b con el volumen con signo de QQQ (Alpaca). Uso: python analizar_alpaca.py [carpeta_datos]"""
import os, sys, glob, numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__)); D = sys.argv[1] if len(sys.argv) > 1 else f"{AQUI}/datos"
rng = np.random.default_rng(10); out = []
def p(s): print(s); out.append(s)
def welch(a, b): return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
q = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(f"{D}/qqq_delta_*.csv"))); q["fecha"] = pd.to_datetime(q.fecha)
q["dz"] = q.delta / q.vol; q["dz5"] = q.delta5 / q.vol5; q["dir"] = np.sign(q.c - q.o)
orb = pd.read_csv(f"{AQUI}/serie_v018_be.csv", parse_dates=["d"]).rename(columns={"d": "fecha"})
x = q.merge(orb, on="fecha"); x = x[(x.dir != 0) & (np.sign(x.dz) != 0)]
ac = np.sign(x.dz) == x.dir; mi = x.fecha < "2022-01-01"
dif = x.Rbe[ac].mean() - x.Rbe[~ac].mean(); t = welch(x.Rbe[ac], x.Rbe[~ac])
h = [x.Rbe[ac & m].mean() - x.Rbe[~ac & m].mean() for m in (mi, ~mi)]
pl = np.percentile([x.Rbe[s].mean() - x.Rbe[~s].mean() for s in (rng.permutation(ac.values) for _ in range(2000))], 95)
ar = np.sign(x.dz5) == x.dir; tr = welch(x.Rbe[ar], x.Rbe[~ar])
ok = dif >= 0.15 and t >= 2.4 and min(h) >= 0.05 and x.Rbe[~ac].mean() <= 0.02 and dif > pl and tr >= 1.5
p(f"Días QQQ {len(q)} ({q.fecha.min().date()} -> {q.fecha.max().date()}), con ORB v018 {len(x)}")
p(f"H2a: acuerdo {ac.sum()} R {x.Rbe[ac].mean():+.3f} | desacuerdo {(~ac).sum()} R {x.Rbe[~ac].mean():+.3f} | dif {dif:+.3f} "
  f"t {t:.2f} | mitades {h[0]:+.3f} {h[1]:+.3f} | placebo p95 {pl:+.3f} | réplica 9:30-9:35 t {tr:.2f} -> {'PASA' if ok else 'NO PASA'}")
y = x[ac]; r = y.dz.abs().rank(pct=True); hi, lo = y.Rbe[r > 2/3], y.Rbe[r <= 1/3]
p(f"H2b: tercio alto {hi.mean():+.3f} (n {len(hi)}) bajo {lo.mean():+.3f} (n {len(lo)}) dif {hi.mean()-lo.mean():+.3f} t {welch(hi, lo):.2f}")
open(f"{AQUI}/analizar_alpaca_salida.txt", "w").write("\n".join(out) + "\n")
