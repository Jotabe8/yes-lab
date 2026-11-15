"""v10: análisis preregistrado (PREREGISTRO_V10.md). Uso: python analizar.py [carpeta_datos]"""
import os, sys, numpy as np, pandas as pd

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "datos")
AQUI = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(10)
COSTE_PT = 0.5


def welch(a, b):
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def tstat(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


# ---- velas NQ -> rasgos por día
m = pd.read_csv(f"{D}/nq_m1.csv.gz"); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["fecha"] = m.t.dt.date; m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute; m = m.set_index(["fecha", "hm"])
def px(col, hm):
    return m[col].xs(hm, level="hm")
dia = pd.DataFrame({"o930": px("open", 930), "c939": px("close", 939), "o931": px("open", 931),
                    "c959": px("close", 959), "o1551": px("open", 1551), "c1559": px("close", 1559)}).dropna()
dia["dir_orb"] = np.sign(dia.c939 - dia.o930)

# ---- desequilibrios
def agreg(f):
    x = pd.read_csv(f); x["fecha"] = pd.to_datetime(x.fecha).dt.date
    tot = x.groupby("fecha").apply(lambda g: g.imb_usd.sum() / g.par_usd.sum() if g.par_usd.sum() > 0 else np.nan)
    q = x[x.symbol == "QQQ"].set_index("fecha"); qqq = q.imb_usd / q.par_usd.replace(0, np.nan)
    return tot, qqq
dia["D_ape"], dia["D_ape_qqq"] = agreg(f"{D}/imbalance_apertura.csv.gz")
dia["D_cie"], dia["D_cie_qqq"] = agreg(f"{D}/imbalance_cierre.csv.gz")
dl = pd.read_csv(f"{D}/nq_delta_0930_0940.csv"); dl["fecha"] = pd.to_datetime(dl.fecha).dt.date; dl = dl.set_index("fecha")
dia["delta"] = (dl.compra - dl.venta) / dl.vol; dia["delta5"] = (dl.compra5 - dl.venta5) / dl.vol5
orb = pd.read_csv(f"{AQUI}/serie_v018_be.csv"); orb["fecha"] = pd.to_datetime(orb.d).dt.date
dia = dia.join(orb.set_index("fecha").Rbe, how="left")
dia.index = pd.to_datetime(dia.index); mitad = dia.index < "2023-01-01"
out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)


def filtro(nom, senal, repl):
    x = dia.dropna(subset=["Rbe", senal]); x = x[(x.dir_orb != 0) & (np.sign(x[senal]) != 0)]
    ac = np.sign(x[senal]) == x.dir_orb
    dif = x.Rbe[ac].mean() - x.Rbe[~ac].mean(); t = welch(x.Rbe[ac], x.Rbe[~ac])
    h = [x.Rbe[ac & mm].mean() - x.Rbe[~ac & mm].mean() for mm in (mitad[dia.index.isin(x.index)], ~mitad[dia.index.isin(x.index)])]
    plac = [x.Rbe[s].mean() - x.Rbe[~s].mean() for s in (rng.permutation(ac.values) for _ in range(2000))]
    xr = x.dropna(subset=[repl]); ar = np.sign(xr[repl]) == xr.dir_orb; tr = welch(xr.Rbe[ar], xr.Rbe[~ar])
    ok = dif >= 0.15 and t >= 2.4 and min(h) >= 0.05 and x.Rbe[~ac].mean() <= 0.02 and dif > np.percentile(plac, 95) \
        and tr >= 1.5
    p(f"{nom}: n={len(x)} acuerdo {ac.sum()} R {x.Rbe[ac].mean():+.3f} | desacuerdo {(~ac).sum()} R {x.Rbe[~ac].mean():+.3f}"
      f" | dif {dif:+.3f} t {t:.2f} | mitades {h[0]:+.3f} {h[1]:+.3f} | placebo p95 {np.percentile(plac, 95):+.3f}"
      f" | réplica t {tr:.2f} -> {'PASA' if ok else 'NO PASA'}")


def sistema(nom, senal, repl, o, c):
    x = dia.dropna(subset=[senal]); x = x[np.sign(x[senal]) != 0]; s = np.sign(x[senal])
    bruto = s * (x[c] - x[o]) / x[o] * 1e4; coste = COSTE_PT / x[o] * 1e4; neto = bruto - coste
    mm = x.index < "2023-01-01"
    plac = [(rng.permutation(s.values) * (x[c] - x[o]) / x[o] * 1e4 - coste).mean() for _ in range(2000)]
    xr = dia.dropna(subset=[repl]); nr = (np.sign(xr[repl]) * (xr[c] - xr[o]) / xr[o] * 1e4 - COSTE_PT / xr[o] * 1e4)
    cor = pd.concat([neto, dia.Rbe], axis=1, sort=True).dropna().corr().iloc[0, 1]
    ok = len(x) >= 150 and tstat(neto) >= 2.4 and neto[mm].mean() > 0 and neto[~mm].mean() > 0 and \
        (bruto - 2 * coste).mean() > 0 and (-bruto - coste).mean() < 0 and neto.mean() > np.percentile(plac, 95) and \
        nr.mean() > 0 and abs(cor) < 0.3
    p(f"{nom}: n={len(x)} bruto {bruto.mean():+.2f} pb neto {neto.mean():+.2f} pb t {tstat(neto):.2f} | mitades "
      f"{neto[mm].mean():+.2f} {neto[~mm].mean():+.2f} | x2 {(bruto - 2*coste).mean():+.2f} | lado contrario "
      f"{(-bruto - coste).mean():+.2f} | placebo p95 {np.percentile(plac, 95):+.2f} | réplica {nr.mean():+.2f} | corr ORB {cor:+.2f}"
      f" -> {'PASA' if ok else 'NO PASA'}")


p(f"Días: {len(dia)}  ({dia.index.min().date()} -> {dia.index.max().date()}); con ORB v018: {dia.Rbe.notna().sum()}")
filtro("H1a filtro desequilibrio apertura", "D_ape", "D_ape_qqq")
sistema("H1b NQ 9:31-9:59 con desequilibrio apertura", "D_ape", "D_ape_qqq", "o931", "c959")
filtro("H2a filtro delta NQ 9:30-9:40", "delta", "delta5")
x = dia.dropna(subset=["Rbe", "delta"]); x = x[np.sign(x.delta) == x.dir_orb]; q = x.delta.abs().rank(pct=True)
hi, lo = x.Rbe[q > 2 / 3], x.Rbe[q <= 1 / 3]
p(f"H2b intensidad (acuerdo): tercio alto {hi.mean():+.3f} (n {len(hi)}) bajo {lo.mean():+.3f} (n {len(lo)}) dif "
  f"{hi.mean() - lo.mean():+.3f} t {welch(hi, lo):.2f}  (listón completo de filtro: ver informe)")
sistema("H3 NQ 15:51-15:59 con desequilibrio cierre", "D_cie", "D_cie_qqq", "o1551", "c1559")
open(f"{AQUI}/analizar_salida.txt", "w").write("\n".join(out) + "\n")
