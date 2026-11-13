"""Réplica del ORB US100 (lógica v017/v018 sin trailing ni filtros): rango 9:30-9:40 NY, dirección de la
vela del rango (cuerpo >= 10 % del rango), entrada 9:40 a mercado (ask/bid), stop 15 % ATR14 diario,
salida 15:55. Stop comprobado en M1 con bid (largos) / ask (cortos). Uso: orb_us100.py dir año salida.csv"""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close"]]

d, anio, salida = sys.argv[1], int(sys.argv[2]), sys.argv[3]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2
t = m.index.hour * 60 + m.index.minute
ses = (t >= 570) & (t < 960)
dias = {}
for f, g in m[ses].groupby(m[ses].index.date):
    dias[f] = g
hl = pd.DataFrame([(f, g.high.max(), g.low.min(), g.close.iloc[-1]) for f, g in dias.items()], columns=["f", "h", "l", "c"]).set_index("f")
pc = hl.c.shift(1)
atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
filas = []
for f, g in dias.items():
    if f.year != anio or not np.isfinite(atr.get(f, np.nan)):
        continue
    tt = g.index.hour * 60 + g.index.minute
    rg = g[tt < 580]
    if len(rg) < 8 or tt[0] != 570:
        continue
    O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
    if H - L <= 0 or abs(C - O) < 0.10 * (H - L):
        continue
    lado = 1 if C > O else -1
    post = g.index[(tt >= 580) & (tt < 955)]
    if len(post) < 300:
        continue
    bb, aa = b.loc[post], a.loc[post]
    ent = aa.open.iloc[0] if lado == 1 else bb.open.iloc[0]
    dist = 0.15 * atr[f]
    stop = ent - lado * dist
    r = None
    for i in range(len(post)):
        if lado == 1 and bb.low.iloc[i] <= stop:
            px = stop if i == 0 else min(stop, bb.open.iloc[i]); r = (px - ent) / dist; break
        if lado == -1 and aa.high.iloc[i] >= stop:
            px = stop if i == 0 else max(stop, aa.open.iloc[i]); r = (ent - px) / dist; break
    if r is None:
        fin = g.index[tt == 955]
        if not len(fin):
            continue
        px = b.loc[fin[0]].open if lado == 1 else a.loc[fin[0]].open
        r = lado * (px - ent) / dist
    filas.append(dict(fecha=f, lado=lado, r=r, atr=atr[f], spread_ent=float(aa.open.iloc[0] - bb.open.iloc[0])))
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.5g")
print(anio, len(filas))
