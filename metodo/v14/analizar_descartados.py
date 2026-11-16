"""Análisis preregistrado v14d (PREREGISTRO_DESCARTADOS.md). Uso: python metodo/v14/analizar_descartados.py [orb|gotobi]"""
import glob, os, sys
import numpy as np, pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
COSTE = {"GER40": 0.0052, "UK100": 0.0079, "JP225": 0.0157, "XAUUSD": 0.0110}
M4 = list(COSTE)
rng = np.random.default_rng(142)
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(*a)
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R

def regimen(fr, cols=("h5", "hhoy")):
    fr = fr.sort_values(["sim", "fecha"]).drop_duplicates(["sim", "fecha"])
    for c in cols:
        fr[f"med_{c}"] = fr.groupby("sim")[c].transform(lambda s: s.shift(1).rolling(250, min_periods=60).median())
    return fr

def sharpe(x, ini, fin):
    d = x.groupby("fecha").n.sum().reindex(pd.bdate_range(ini, fin), fill_value=0)
    return d.mean() / d.std() * np.sqrt(252)

def evaluar(nombre, b, col, mercados, deciden):
    p(f"\n===== {nombre} · {col} =====")
    b = b[b[col].notna() & b[f"med_{col}"].notna()].copy()
    b["pers"] = b[col] >= b[f"med_{col}"]
    f = b[b.pers]; bd = b[b.sim.isin(deciden)]; fd = f[f.sim.isin(deciden)]
    for nom, x in [("Base", b), ("Persistente", f), ("Antipersistente", b[~b.pers])]:
        p(f"  {nom:16s} n {len(x):5d} | bruto {x.r.mean():+.3f} | neto {x.n.mean():+.3f} (t {tstat(x.n):5.2f}) | x2 {x.n2.mean():+.3f}")
    pos = 0; mej_rep = []
    for s in mercados:
        x = b[b.sim == s]; y = x[x.pers]
        pos += y.n.mean() > 0; mej_rep.append(y.r.mean() - x.r.mean())
        p(f"    {s}: base neto {x.n.mean():+.3f} | pers neto {y.n.mean():+.3f} (t {tstat(y.n):.2f}, n {len(y)}) | anti {x[~x.pers].n.mean():+.3f} | mejora bruta {y.r.mean()-x.r.mean():+.3f}")
    grupos = {s: bd[bd.sim == s].n.values for s in deciden}; tam = fd.groupby("sim").size().to_dict()
    med = np.array([np.concatenate([rng.choice(grupos[s], tam.get(s, 0), replace=False) for s in deciden]).mean() for _ in range(2000)])
    p99 = np.percentile(med, 99); pv = (med >= fd.n.mean()).mean()
    c = pd.Timestamp("2019-07-01")
    mej = [fd[fd.fecha < c].n.mean() - bd[bd.fecha < c].n.mean(), fd[fd.fecha >= c].n.mean() - bd[bd.fecha >= c].n.mean()]
    ini, fin = bd.fecha.min(), bd.fecha.max(); shb, shf = sharpe(bd, ini, fin), sharpe(fd, ini, fin)
    dia = fd.groupby("fecha").n.sum()
    j = pd.concat([dia.rename("x"), v.rename("v")], axis=1).loc["2018-01-23":"2026-11-13"].fillna(0); corr = j.corr().iloc[0, 1]
    if len(deciden) > 1: c6 = (f"6 mercados + ({pos}/{len(mercados)})", pos >= 3)
    else: c6 = (f"6 réplicas con mejora bruta > 0 ({', '.join(f'{m:+.3f}' for m in mej_rep[1:])})", all(m > 0 for m in mej_rep[1:]))
    crit = {f"1 t neto filtrado >= 2,4 ({tstat(fd.n):.2f})": tstat(fd.n) >= 2.4,
            f"2 placebo p99 {p99:+.3f} (p-valor {pv:.3f})": fd.n.mean() > p99,
            f"3 mejora en las 2 mitades ({mej[0]:+.3f} / {mej[1]:+.3f})": min(mej) > 0,
            "4 costes x2 > 0": fd.n2.mean() > 0,
            f"5 Sharpe filtrado > base ({shf:.2f} vs {shb:.2f})": shf > shb,
            c6[0]: c6[1], f"7 corr v018 ({corr:+.2f}) < 0,3": abs(corr) < 0.3}
    for k, ok in crit.items(): p(f"  {'SÍ' if ok else 'NO'}  {k}")
    pasa = all(crit.values()); p("  VEREDICTO:", "PASA" if pasa else "NO PASA")
    return pasa

res = {}
que = sys.argv[1] if len(sys.argv) > 1 else "orb"
if que == "orb":
    base = pd.concat([pd.read_csv(x) for x in glob.glob(f"{D}/base/*.csv")]); base["fecha"] = pd.to_datetime(base.fecha)
    fr = pd.concat([pd.read_csv(x) for x in glob.glob(f"{D}/datos/*.csv")]); fr["fecha"] = pd.to_datetime(fr.fecha)
    df = base.merge(regimen(fr), on=["sim", "fecha"], how="left")
    df = df[(df.fecha >= "2012-03-01") & df.lado.notna() & df.sim.isin(M4)].copy()
    df["c"] = df.sim.map(COSTE) / 100 * df.px / df.dist; df["n"] = df.r - df.c; df["n2"] = df.r - 2 * df.c
    for col in ["h5", "hhoy"]: res[f"ORB-{col}"] = evaluar("1. ORB sin condición GER40+UK100+JP225+oro", df, col, M4, M4)
else:
    g = pd.concat([pd.read_csv(x) for x in glob.glob(f"{D}/gotobi/*.csv")]); g["fecha"] = pd.to_datetime(g.fecha)
    g = regimen(g)  # mediana sobre TODOS los días hábiles
    g = g[(g.fecha >= "2012-03-01") & (g.gotobi == 1)].copy()
    PIP = 0.01
    g["c"] = 0.5 * PIP / g.dist; g["n"] = g.r - g.c; g["n2"] = g.r - g.c - 1.6 * PIP / g.dist
    p("Gotobi bruto por par (todos los días gotobi):", g.groupby("sim").r.mean().round(3).to_dict(),
      "| neto USDJPY", round(g[g.sim == "USDJPY"].n.mean(), 3), "t", round(tstat(g[g.sim == "USDJPY"].n), 2))
    for col in ["h5", "hhoy"]: res[f"GOTOBI-{col}"] = evaluar("2. Gotobi (decide USDJPY)", g, col, ["USDJPY", "EURJPY", "GBPJPY"], ["USDJPY"])
p("\nRESUMEN:", {k: ("PASA" if x else "no") for k, x in res.items()})
open(f"{D}/salida_descartados_{que}.txt", "w").write("\n".join(out) + "\n")
