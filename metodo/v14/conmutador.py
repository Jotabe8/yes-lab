"""v14b conmutador por Hurst (PREREGISTRO_CONMUTADOR.md). Uso: python metodo/v14/conmutador.py"""
import glob, os
import numpy as np, pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
COSTE = {"GER40": 0.0052, "UK100": 0.0079, "JP225": 0.0157, "XAUUSD": 0.0110, "US100": 0.0049}
M4 = ["GER40", "UK100", "JP225", "XAUUSD"]
rng = np.random.default_rng(141)
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(*a)
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

base = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/base/*.csv")]); base["fecha"] = pd.to_datetime(base.fecha)
fr = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/datos/*.csv")]); fr["fecha"] = pd.to_datetime(fr.fecha)
fr = fr.sort_values(["sim", "fecha"]).drop_duplicates(["sim", "fecha"])
for c in ["h5", "hhoy"]:
    fr[f"med_{c}"] = fr.groupby("sim")[c].transform(lambda s: s.shift(1).rolling(250, min_periods=60).median())
df = base.merge(fr, on=["sim", "fecha"], how="left")
df = df[(df.fecha >= "2012-03-01") & df.lado.notna() & df.r_contra.notna()].copy()
df["c"] = df.sim.map(COSTE) / 100 * df.px / df.dist
v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R

def evaluar(col, mercados, liston=2.64):
    b = df[df.sim.isin(mercados) & df[col].notna() & df[f"med_{col}"].notna()].copy()
    pers = (b[col] >= b[f"med_{col}"]).values
    def neto(pe, k=1):
        return np.where(pe, b.r.values, b.r_contra.values) - k * b.c.values
    b["n"] = neto(pers); b["n2"] = neto(pers, 2); b["pers"] = pers
    p(f"\n===== Conmutador {col} · {'+'.join(mercados)} =====")
    p(f"  n {len(b)} | neto {b.n.mean():+.3f} (t {tstat(b.n):.2f}) | x2 {b.n2.mean():+.3f}")
    ps, an = b[b.pers], b[~b.pers]
    p(f"  pata sigue (persistente): {ps.n.mean():+.3f} (n {len(ps)}, t {tstat(ps.n):.2f}) | pata contra (antipers.): {an.n.mean():+.3f} (n {len(an)}, t {tstat(an.n):.2f})")
    p(f"  referencia: ORB siempre {(b.r - b.c).mean():+.3f} | contra siempre {(b.r_contra - b.c).mean():+.3f}")
    pos = 0
    for s in mercados:
        x = b[b.sim == s]; pos += x.n.mean() > 0
        p(f"    {s}: neto {x.n.mean():+.3f} (n {len(x)}) | sigue {x[x.pers].n.mean():+.3f} | contra {x[~x.pers].n.mean():+.3f}")
    # placebo: permutar la etiqueta dentro de cada mercado
    idx = {s: np.where(b.sim.values == s)[0] for s in mercados}
    med = []
    for _ in range(2000):
        pe = pers.copy()
        for s, ii in idx.items(): pe[ii] = rng.permutation(pers[ii])
        med.append(neto(pe).mean())
    p99 = np.percentile(med, 99)
    m2 = b[b.fecha >= "2019-07-01"].n.mean()
    dia = b.groupby("fecha").n.sum()
    j = pd.concat([dia.rename("x"), v.rename("v")], axis=1).loc["2018-01-23":"2026-11-13"].fillna(0)
    corr = j.corr().iloc[0, 1]
    crit = {f"1 t neto >= {liston}": tstat(b.n) >= liston,
            f"2 placebo permutación (p99 {p99:+.3f}, p50 {np.median(med):+.3f})": b.n.mean() > p99,
            f"3 2.ª mitad > 0 ({m2:+.3f})": m2 > 0, "4 costes x2 > 0": b.n2.mean() > 0,
            f"5 mercados + ({pos}/{len(mercados)})": pos >= min(3, len(mercados)),
            "6 las dos patas > 0": ps.n.mean() > 0 and an.n.mean() > 0,
            f"7 corr v018 ({corr:+.2f}) < 0,3": abs(corr) < 0.3}
    for k, ok in crit.items(): p(f"  {'SÍ' if ok else 'NO'}  {k}")
    pasa = all(crit.values()); p("  VEREDICTO:", "PASA" if pasa else "NO PASA")
    serie = dia.reindex(pd.bdate_range(dia.index.min(), dia.index.max()), fill_value=0).values
    nb = len(serie) // 20; bl = serie[: nb * 20].reshape(nb, 20); mus, dds = [], []
    for _ in range(2000):
        s = bl[rng.integers(0, nb, nb)].ravel(); cc = np.cumsum(s)
        mus.append(s.mean()); dds.append((np.maximum.accumulate(cc) - cc).max())
    p(f"  MC: P(media<=0) {np.mean(np.array(mus) <= 0):.3f} | DD p95 {np.percentile(dds, 95):.1f} R | R/año {serie.mean()*252:+.1f} | Sharpe {serie.mean()/serie.std()*np.sqrt(252):.2f}")
    return pasa

r = {c: evaluar(c, M4) for c in ["h5", "hhoy"]}
p("\n== Informativo US100 (no decide) ==")
for c in ["h5", "hhoy"]: evaluar(c, ["US100"])
p("\nRESUMEN:", {k: ("PASA" if x else "no") for k, x in r.items()})
open(f"{D}/salida_conmutador.txt", "w").write("\n".join(out) + "\n")
