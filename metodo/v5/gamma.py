"""Prueba preregistrada v5-1 (PREREGISTRO_GAMMA.md): gamma de creadores de mercado y última media hora."""
import sys, glob
import numpy as np, pandas as pd

D = "metodo/v5/datos"
COSTE = 1.0  # pb ida y vuelta
rng = np.random.default_rng(14112026)

def gex():
    g = pd.read_csv(f"{D}/DIX.csv")
    g.columns = [c.strip().lower() for c in g.columns]
    g["date"] = pd.to_datetime(g["date"])
    return g.set_index("date")["gex"].astype(float).sort_index()

def barras(sim):
    fs = [f"orb_acciones/indices_2012/{sim}_b30.csv"] + sorted(glob.glob(f"{D}/{sim}_b30*.csv"))
    b = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["fecha", "bar"])
    b["fecha"] = pd.to_datetime(b["fecha"])
    p = b.pivot(index="fecha", columns="bar")
    ok = p["o"].notna().all(axis=1) & p["c"].notna().all(axis=1) & (p["n"][12] >= 25)
    p = p[ok]
    rpre = np.log(p["c"][11] / p["o"][0]) * 1e4
    rlast = np.log(p["c"][12] / p["o"][12]) * 1e4
    return pd.DataFrame({"rpre": rpre, "rlast": rlast}).sort_index()

def con_gex(df, g):
    # GEX del último día publicado ANTES de la fecha de operación
    prev = g.copy(); prev.index = prev.index + pd.Timedelta(days=1)
    x = pd.merge_asof(df.reset_index().rename(columns={"fecha": "d"}), prev.rename("gex").reset_index().rename(columns={"date": "d"}),
                      on="d", direction="backward").set_index("d")
    pct = g.rolling(252, min_periods=126).apply(lambda v: (v[:-1] < v[-1]).mean() if len(v) > 1 else np.nan, raw=True)
    pp = pct.copy(); pp.index = pp.index + pd.Timedelta(days=1)
    x = pd.merge_asof(x.reset_index(), pp.rename("pct").reset_index().rename(columns={"date": "d"}), on="d",
                      direction="backward").set_index("d")
    return x.dropna(subset=["gex"])

def tstat(v):
    v = np.asarray(v); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 2 else np.nan

def informe(x, mask, signo=1, nombre=""):
    s = x[mask]
    bruto = signo * np.sign(s.rpre) * s.rlast
    neto, neto2 = bruto - COSTE, bruto - 2 * COSTE
    mitad = s.index[len(s) // 2] if len(s) else None
    seg = neto[s.index >= mitad] if len(s) else neto
    pri = neto[s.index < mitad] if len(s) else neto
    rec = neto[s.index >= "2023-01-01"]
    print(f"{nombre}: n {len(s)} ({len(s)/((x.index[-1]-x.index[0]).days/365.25):.1f}/año) bruto {bruto.mean():+.2f} pb "
          f"neto {neto.mean():+.2f} t {tstat(neto):+.2f} | x2 {neto2.mean():+.2f} | 1ª mitad {pri.mean():+.2f} "
          f"2ª mitad {seg.mean():+.2f} | 2023-26 {rec.mean():+.2f} (n {len(rec)})")
    return bruto, neto

def placebo(x, n):
    tot = (np.sign(x.rpre) * x.rlast).values
    return np.percentile([rng.choice(tot, n, replace=False).mean() for _ in range(2000)], 95)

def cola(x, neto):
    dia = pd.Series(0.0, index=x.index); dia[neto.index] = neto.values / 1e4
    esc = 0.15 / (dia.std() * np.sqrt(252)); r = dia * esc
    eq = r.cumsum(); dd = (eq.cummax() - eq).max(); anual = r.mean() * 252
    return dd, anual

def corr_orb(neto):
    o = pd.read_csv(f"{D}/serie_v018_be.csv", parse_dates=["d"]).set_index("d")["R"]
    j = pd.concat([o, neto.rename("g")], axis=1, sort=True).fillna(0)
    j = j[j.index >= o.index[0]]
    return j.corr().iloc[0, 1]

g = gex()
print(f"GEX: {g.index[0].date()} → {g.index[-1].date()}, {len(g)} días; días GEX<0: {(g<0).sum()}")
for sim in ["US500", "US100"]:
    x = con_gex(barras(sim), g)
    print(f"\n=== {sim}: {x.index[0].date()} → {x.index[-1].date()}, {len(x)} días ===")
    neg = x.gex < 0
    bruto, neto = informe(x, neg, 1, "PRINCIPAL GEX<0 seguir")
    if len(bruto) == 0:
        continue
    p95 = placebo(x, len(bruto))
    dd, an = cola(x, neto)
    sh = neto[neto.index >= neto.index[len(neto)//2]].mean()
    print(f"placebo p95 bruto {p95:+.2f} pb (real {bruto.mean():+.2f}) | cola: DD {dd*100:.1f} % vs 3×anual {3*an*100:.1f} % "
          f"| corr ORB v018 {corr_orb(neto):+.3f}")
    if sim == "US500":
        lis = [tstat(neto) >= 2.4, sh > 0, (bruto - 2*COSTE).mean() > 0, bruto.mean() > p95, dd < 3*an, len(neto) >= 150]
        print("LISTÓN US500 (t≥2,4, 2ª mitad>0, ×2>0, >placebo, cola, n≥150):", lis, "→", "PASA" if all(lis) else "NO PASA")
    else:
        print("RÉPLICA US100 (neto>0 y t≥1,5):", neto.mean() > 0 and tstat(neto) >= 1.5)
    informe(x, ~neg, 1, "info GEX≥0 seguir")
    informe(x, x.pct <= 0.2, 1, "I1 GEX 20 % bajo seguir")
    informe(x, x.pct >= 0.8, -1, "I2 GEX 20 % alto contra")
    informe(x, x.index == x.index, 1, "info todos los días seguir")
