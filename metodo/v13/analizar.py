"""Análisis preregistrado v13 (PREREGISTRO_ORB_EN_JUEGO.md). Uso: python metodo/v13/analizar.py"""
import glob, os
import numpy as np, pandas as pd

D = os.path.dirname(__file__)
COSTE = {"GER40": 0.0052, "UK100": 0.0079, "JP225": 0.0157, "XAUUSD": 0.0110, "USOIL": 0.0500, "US100": 0.0049}
CARTERA = ["GER40", "UK100", "JP225", "XAUUSD", "USOIL"]
rng = np.random.default_rng(13)

def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

df = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/datos/*.csv")])
df["fecha"] = pd.to_datetime(df.fecha)
df = df[df.fecha >= "2012-03-01"].sort_values(["sim", "fecha"])
df["c"] = df.sim.map(COSTE) / 100 * df.px / df.dist
df["n"] = df.r - df.c; df["n2"] = df.r - 2 * df.c; df["nc"] = df.r_contra - df.c
sen = df[df.lado.notna()].copy()
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(*a)

p("== Volumen útil por mercado (fracción de tramos con volumen 0 o NaN) ==")
cero = df.groupby("sim").apply(lambda g: ((g.vr.fillna(0) <= 0)).mean())
p(cero.round(3).to_dict())
validos_v1 = [s for s in CARTERA if cero.get(s, 1) <= 0.20]
p("Mercados en V1:", validos_v1)

def linea(nom, x):
    if len(x) < 3: p(f"{nom:34s} n {len(x)}"); return
    p(f"{nom:34s} n {len(x):5d} | bruto {x.r.mean():+.3f} (t {tstat(x.r):5.2f}) | coste {x.c.mean():.3f} | neto {x.n.mean():+.3f} (t {tstat(x.n):5.2f}) | x2 {x.n2.mean():+.3f} | contra {x.nc.mean():+.3f}")

def evaluar(nombre, col, mercados, liston):
    p(f"\n===== {nombre} (umbral {col} >= 1,5; listón t {liston}) =====")
    linea("Incondicional (todos los días)", sen[sen.sim.isin(mercados)])
    ej = sen[sen.sim.isin(mercados) & (sen[col] >= 1.5)]
    linea("EN JUEGO cartera", ej)
    for s in mercados + (["US100"] if "US100" not in mercados else []):
        linea(f"  {s} en juego", sen[(sen.sim == s) & (sen[col] >= 1.5)])
        linea(f"  {s} incondicional", sen[sen.sim == s])
    m1, m2 = ej[ej.fecha < "2019-07-01"], ej[ej.fecha >= "2019-07-01"]
    linea("  1.ª mitad", m1); linea("  2.ª mitad", m2)
    p("  Por año neto:", ej.groupby(ej.fecha.dt.year).n.mean().round(3).to_dict())
    # placebo de días
    medias = []
    grupos = {s: sen[sen.sim == s].n.values for s in mercados}
    tam = ej.groupby("sim").size().to_dict()
    for _ in range(2000):
        x = np.concatenate([rng.choice(grupos[s], tam.get(s, 0), replace=False) for s in mercados])
        medias.append(x.mean())
    p95 = np.percentile(medias, 95)
    # correlación con v018
    v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
    dia = ej.groupby("fecha").n.sum()
    j = pd.concat([dia, v], axis=1).fillna(0)
    j = j[(j.index >= max(v.index.min(), dia.index.min()))]
    corr = j.corr().iloc[0, 1]
    pos = sum(sen[(sen.sim == s) & (sen[col] >= 1.5)].n.mean() > 0 for s in mercados)
    crit = {"1 t neto": tstat(ej.n) >= liston, "2 2.ª mitad > 0": m2.n.mean() > 0, "3 costes x2 > 0": ej.n2.mean() > 0,
            f"4 placebo días (p95 {p95:+.3f})": ej.n.mean() > p95, "5 lado contrario < 0": ej.nc.mean() < 0,
            f"6 mercados + ({pos}/{len(mercados)})": pos >= 3, f"7 corr v018 ({corr:+.2f})": abs(corr) < 0.3}
    for k, b in crit.items(): p(f"  {'SÍ' if b else 'NO'}  {k}")
    pasa = all(crit.values()); p("  VEREDICTO:", "PASA" if pasa else "NO PASA")
    # Monte Carlo por bloques de 20 días sobre la serie diaria (todas las fechas hábiles)
    serie = dia.reindex(pd.bdate_range(dia.index.min(), dia.index.max()), fill_value=0).values
    nb = len(serie) // 20; bl = serie[: nb * 20].reshape(nb, 20)
    mus, dds = [], []
    for _ in range(2000):
        s = bl[rng.integers(0, nb, nb)].ravel(); c = np.cumsum(s)
        mus.append(s.mean()); dds.append((np.maximum.accumulate(c) - c).max())
    p(f"  MC: P(media<=0) {np.mean(np.array(mus) <= 0):.3f} | peor DD p50 {np.median(dds):.1f} R p95 {np.percentile(dds,95):.1f} R | R/año {serie.mean()*252:+.1f}")
    return pasa

evaluar("V1 VOLUMEN (principal)", "rvol", validos_v1, 2.4)
evaluar("V2 RANGO", "rrango", CARTERA, 2.64)
open(f"{D}/salida_v13.txt", "w").write("\n".join(out) + "\n")
