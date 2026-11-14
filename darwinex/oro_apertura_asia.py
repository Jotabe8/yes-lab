"""Preregistro 2: oro largo 19:00→22:00 NY, confirmación en 2003-2011 (PREREGISTRO_ORO_ASIA.md)."""
import sys, numpy as np, pandas as pd
sys.argv = ["x", sys.argv[1] if len(sys.argv) > 1 else "datos_oro/antes2012"]
exec(open("darwinex/oro_asia.py").read().split("res = {}")[0].replace("def informe", "def _no"))

def prueba(ins):
    o = serie(ins)
    print(f"\n===== {ins.upper()} {o.index[0].date()} → {o.index[-1].date()} ({len(o)} barras) =====")
    v = ventanas(o, 19, 3); v = v[v.index.dayofweek.isin([6, 0, 1, 2, 3])]
    a, n = t(v); print(f"PRINCIPAL 19→22 NY: bruto {bp(v.mean())} t {a:.2f} n {n}")
    for nom, s in (("2003-07", v.loc[:"2007"]), ("2008-11", v.loc["2008":])):
        a, m = t(s); print(f"   {nom}: {bp(s.mean())} t {a:.2f} n {m}")
    for c in (0.5e-4, 1e-4, 2e-4):
        a, _ = t(v - c); print(f"   neta coste {c*1e4:.1f} pb: {bp((v - c).mean())} t {a:.2f}")
    print("   año a año:", " ".join(f"{y}:{s.mean()*1e4:+.2f}" for y, s in v.groupby(v.index.year)))
    pl = {}
    for h in range(24):
        s = ventanas(o, h, 3); s = s[s.index.dayofweek.isin([6, 0, 1, 2, 3, 4])]; pl[h] = s.mean() * 1e4
    pl = pd.Series(pl); print("   placebo 3 h por hora de inicio (pb):", pl.round(2).to_dict())
    print(f"   mediana placebo {pl.median():+.2f} pb; 19:00 queda {(pl > pl[19]).sum() + 1}ª de 24")
    r = np.log(o).diff(); r[(o.index.to_series().diff() > pd.Timedelta("1h")).values] = np.nan
    print("   hora a hora (pb):", (r.groupby(r.index.hour).mean() * 1e4).round(2).to_dict())

for ins in ("xauusd", "xagusd"):
    try: prueba(ins)
    except Exception as e: print("falla", ins, e)
