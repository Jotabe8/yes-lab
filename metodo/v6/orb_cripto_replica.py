"""Réplica preregistrada (PREREGISTRO_ORB_CRIPTO_REPLICA.md). Uso: python orb_cripto_replica.py SYM salida.csv
Descarga las velas M1 de los perpetuos USDT-M de Binance y aplica la regla de metodo/v3/orb_cripto_medio.py (L=10)
a las 9:30 NY y a la 01:00 NY (placebo de hora)."""
import sys, io, zipfile, urllib.request
import numpy as np, pandas as pd

sym, salida = sys.argv[1], sys.argv[2]
meses = pd.period_range("2020-12", "2026-10", freq="M")
partes = []
for p in meses:
    url = f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1m/{sym}-1m-{p.year}-{p.month:02d}.zip"
    try:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=60).read()))
    except Exception as e:
        print("falta", p, e); continue
    df = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=range(5), dtype=str)
    df = df[pd.to_numeric(df[0], errors="coerce").notna()].astype(float)
    partes.append(df)
k = pd.concat(partes).drop_duplicates(0).sort_values(0)
ts = k[0].where(k[0] < 1e14, k[0] / 1000)
k.index = pd.to_datetime(ts, unit="ms", utc=True).dt.tz_convert("America/New_York")
m = k[[1, 2, 3, 4]].set_axis(["open", "high", "low", "close"], axis=1)

def tramo(g, lado, ent, dist):
    stop = ent - lado * dist
    lo, hi, op = g.low.values, g.high.values, g.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop:
            return ((stop if i == 0 else min(stop, op[i])) - ent) / dist
        if lado == -1 and hi[i] >= stop:
            return (ent - (stop if i == 0 else max(stop, op[i]))) / dist
    return lado * (op[-1] - ent) / dist

t = m.index.hour * 60 + m.index.minute
res = {}
for S0, nom in ((570, "ny"), (60, "h01")):
    ses = (t >= S0) & (t < S0 + 390)
    dias = {f: g for f, g in m[ses].groupby(m[ses].index.date)}
    hl = pd.DataFrame([(f, g.high.max(), g.low.min(), g.close.iloc[-1]) for f, g in dias.items()], columns=["f", "h", "l", "c"]).set_index("f")
    pc = hl.c.shift(1)
    atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    for f, g in dias.items():
        if pd.Timestamp(f).dayofweek >= 5 or not np.isfinite(atr.get(f, np.nan)):
            continue
        tt = g.index.hour * 60 + g.index.minute
        if tt[0] != S0 or (tt == S0 + 385).sum() == 0:
            continue
        dist = 0.15 * atr[f]; rg = g[tt < S0 + 10]
        O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
        if len(rg) < 8 or H - L <= 0 or abs(C - O) < 0.10 * (H - L):
            continue
        lado = 1 if C > O else -1
        post = g[(tt >= S0 + 10) & (tt <= S0 + 385)]
        ent = post.open.iloc[0]
        d = res.setdefault(f, dict(fecha=f, sim=sym))
        d[f"r_{nom}"], d[f"c_{nom}"], d[f"lado_{nom}"] = tramo(post, lado, ent, dist), tramo(post, -lado, ent, dist), lado
        d[f"stop_pct_{nom}"] = dist / ent
pd.DataFrame(list(res.values())).sort_values("fecha").to_csv(salida, index=False, float_format="%.5g")
print(sym, len(res))
