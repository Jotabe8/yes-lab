"""Análisis preregistrado v14 (PREREGISTRO_FRACTALES.md). Uso: python metodo/v14/analizar.py"""
import glob, os
import numpy as np, pandas as pd

D = os.path.dirname(__file__)
COSTE = {"GER40": 0.0052, "UK100": 0.0079, "JP225": 0.0157, "XAUUSD": 0.0110, "US100": 0.0049}
B4 = ["GER40", "UK100", "JP225", "XAUUSD"]
rng = np.random.default_rng(14)
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(*a)
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

base = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/base/*.csv")]); base["fecha"] = pd.to_datetime(base.fecha)
fr = pd.concat([pd.read_csv(f) for f in glob.glob(f"{D}/datos/*.csv")]); fr["fecha"] = pd.to_datetime(fr.fecha)
fr = fr.sort_values(["sim", "fecha"]).drop_duplicates(["sim", "fecha"])
# régimen: H >= mediana de los 250 días anteriores del mismo mercado (mínimo 60)
for c in ["h5", "hhoy", "hrs5", "dh5"]:
    fr[f"med_{c}"] = fr.groupby("sim")[c].transform(lambda s: s.shift(1).rolling(250, min_periods=60).median())
df = base.merge(fr, on=["sim", "fecha"], how="left")
df = df[(df.fecha >= "2012-03-01") & df.lado.notna()].copy()
df["c"] = df.sim.map(COSTE) / 100 * df.px / df.dist
df["n"] = df.r - df.c; df["n2"] = df.r - 2 * df.c

p("Cobertura de medidas (fracción de días con señal con H y mediana):")
for c in ["h5", "hhoy"]:
    p(" ", c, df.groupby("sim").apply(lambda g: g[f"med_{c}"].notna().mean()).round(3).to_dict())
p("Media de H por mercado:", df.groupby("sim")[["h5", "hhoy"]].mean().round(3).to_dict())

def sharpe_diario(x, ini, fin):
    dia = x.groupby("fecha").n.sum().reindex(pd.bdate_range(ini, fin), fill_value=0)
    return dia.mean() / dia.std() * np.sqrt(252)

def linea(nom, x):
    p(f"  {nom:30s} n {len(x):5d} | bruto {x.r.mean():+.3f} | neto {x.n.mean():+.3f} (t {tstat(x.n):5.2f}) | x2 {x.n2.mean():+.3f}")

def evaluar(nombre, b, col, mercados):
    p(f"\n===== {nombre} · medida {col} =====")
    b = b[b[f"med_{col}"].notna() & b[col].notna()].copy()
    b["pers"] = b[col] >= b[f"med_{col}"]
    f = b[b.pers]; a = b[~b.pers]
    linea("Base (régimen definido)", b); linea("PERSISTENTE (filtrado)", f); linea("Antipersistente", a)
    for s in mercados:
        x, y = b[b.sim == s], f[f.sim == s]
        p(f"    {s}: base {x.n.mean():+.3f} (n {len(x)}) | pers {y.n.mean():+.3f} (n {len(y)}) | anti {x[~x.pers].n.mean():+.3f}")
    grupos = {s: b[b.sim == s].n.values for s in mercados}; tam = f.groupby("sim").size().to_dict()
    med = np.array([np.concatenate([rng.choice(grupos[s], tam.get(s, 0), replace=False) for s in mercados]).mean() for _ in range(2000)])
    p99 = np.percentile(med, 99)
    corte = pd.Timestamp("2019-07-01")
    mej = [f[m].n.mean() - b[m2].n.mean() for m, m2 in
           [(f.fecha < corte, b.fecha < corte), (f.fecha >= corte, b.fecha >= corte)]]
    ini, fin = b.fecha.min(), b.fecha.max()
    shb, shf = sharpe_diario(b, ini, fin), sharpe_diario(f, ini, fin)
    b["ter"] = b.groupby("sim")[col].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    ter = b.groupby("ter").n.mean()
    p("  Tercios de H (bajo→alto) neto:", ter.round(3).to_dict())
    crit = {"1 t neto filtrado >= 2,4": tstat(f.n) >= 2.4,
            f"2 placebo (p99 {p99:+.3f}, p50 {np.median(med):+.3f})": f.n.mean() > p99,
            f"3 mejora en las 2 mitades ({mej[0]:+.3f} / {mej[1]:+.3f})": min(mej) > 0,
            "4 costes x2 > 0": f.n2.mean() > 0,
            f"5 Sharpe filtrado > base ({shf:.2f} vs {shb:.2f})": shf > shb,
            "6 tercio alto > tercio bajo": ter.iloc[-1] > ter.iloc[0]}
    for k, v in crit.items(): p(f"  {'SÍ' if v else 'NO'}  {k}")
    pasa = all(crit.values()); p("  VEREDICTO:", "PASA" if pasa else "NO PASA")
    # informativos: tamaño 1,5/0,5 y Monte Carlo del filtrado
    b["nt"] = np.where(b.pers, 1.5, 0.5) * b.n
    dia_t = b.groupby("fecha").nt.sum().reindex(pd.bdate_range(ini, fin), fill_value=0)
    p(f"  Inf. tamaño 1,5/0,5: Sharpe {dia_t.mean()/dia_t.std()*np.sqrt(252):.2f} (base {shb:.2f})")
    serie = f.groupby("fecha").n.sum().reindex(pd.bdate_range(ini, fin), fill_value=0).values
    nb = len(serie) // 20; bl = serie[: nb * 20].reshape(nb, 20); mus, dds = [], []
    for _ in range(2000):
        s = bl[rng.integers(0, nb, nb)].ravel(); cc = np.cumsum(s)
        mus.append(s.mean()); dds.append((np.maximum.accumulate(cc) - cc).max())
    p(f"  MC filtrado: P(media<=0) {np.mean(np.array(mus) <= 0):.3f} | DD p95 {np.percentile(dds, 95):.1f} R | R/año {serie.mean()*252:+.1f}")
    return pasa, b

res = {}
A = df[df.sim == "US100"]
Bc = df[df.sim.isin(B4) & (df.rrango >= 1.5)]
for col in ["h5", "hhoy"]:
    res[("A", col)], bA = evaluar("A. ORB US100 (réplica 2012-26)", A, col, ["US100"])
    res[("B", col)], _ = evaluar("B. ORB en juego GER40+UK100+JP225+oro", Bc, col, B4)
    # informativo: v018 real 2018-26 con el mismo régimen
    v = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).rename(columns={"d": "fecha"})
    reg = bA[["fecha", "pers"]]
    j = v.merge(reg, on="fecha", how="inner"); j = j[j.R != 0]
    p(f"  Inf. v018 real 2018-26 ({len(j)} ops): pers {j[j.pers].R.mean():+.3f} (t {tstat(j[j.pers].R):.2f}) | anti {j[~j.pers].R.mean():+.3f} (t {tstat(j[~j.pers].R):.2f})")

p("\n== Informativas (no deciden) ==")
for col in ["hrs5", "dh5"]:
    for nom, b in [("A US100", A), ("B en juego", Bc)]:
        x = b[b[f"med_{col}"].notna()]; alto = x[col] >= x[f"med_{col}"]
        p(f"  {col} {nom}: alto {x[alto].n.mean():+.3f} (n {alto.sum()}) | bajo {x[~alto].n.mean():+.3f} (n {(~alto).sum()})")
p("\nRESUMEN:", {f"{k[0]}-{k[1]}": ("PASA" if v else "no") for k, v in res.items()})
open(f"{D}/salida_v14.txt", "w").write("\n".join(out) + "\n")
