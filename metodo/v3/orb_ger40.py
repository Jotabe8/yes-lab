"""ORB GER40 (preregistro metodo/v3/PREREGISTRO_ORB_GER40.md).
Uso: orb_ger40.py dir_velas año salida.csv. M1 bid/ask Dukascopy -> precio medio, hora de Fráncfort."""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True)
    return df[["open", "high", "low", "close"]]

def tramo(g, lado, ent, dist, be=0.0):
    stop = ent - lado * dist
    lo, hi, op = g.low.values, g.high.values, g.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop: return ((stop if i == 0 else min(stop, op[i])) - ent) / dist
        if lado == -1 and hi[i] >= stop: return (ent - (stop if i == 0 else max(stop, op[i]))) / dist
        if be and lado == 1 and hi[i] >= ent + be * dist: stop = max(stop, ent)
        if be and lado == -1 and lo[i] <= ent - be * dist: stop = min(stop, ent)
    return lado * (g.close.values[-1] - ent) / dist

d, anio, salida = sys.argv[1], int(sys.argv[2]), sys.argv[3]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2; spr = a.close - b.close
# ATR(14) diario con días del servidor FTMO (NY + 7 h)
srv = m.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
dd = m.groupby(srv.date).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
pc = dd.c.shift(1)
atr = pd.concat([dd.h - dd.l, (dd.h - pc).abs(), (dd.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
loc = m.index.tz_convert("Europe/Berlin"); m.index = loc; spr.index = loc
fechas = loc.date

def orb(g, t, ini, dist):
    rg = g[(t >= ini) & (t < ini + 10)]
    if len(rg) < 7: return None
    O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
    if H - L <= 0 or abs(C - O) < 0.1 * (H - L): return None
    lado = 1 if C > O else -1
    post = g[(t >= ini + 10) & (t < 17 * 60 + 25)]
    if len(post) < 10: return None
    ent = post.open.iloc[0]
    return lado, tramo(post, lado, ent, dist), tramo(post, -lado, ent, dist), tramo(post, lado, ent, dist, 2.0), ent

filas = []
for f, g in m.groupby(fechas):
    if f.year != anio or f.weekday() >= 5 or not np.isfinite(atr.get(f, np.nan)): continue
    t = g.index.hour * 60 + g.index.minute
    dist = 0.15 * atr[f]
    fila = dict(fecha=f, atr=atr[f], dist=dist)
    x = orb(g, t, 9 * 60, dist)
    if x: fila.update(lado=x[0], r=x[1], r_contra=x[2], r_be2=x[3], px=x[4])
    y = orb(g, t, 11 * 60, dist)
    if y: fila.update(r_hora=y[1])
    sp = spr.loc[g.index][(t >= 9 * 60) & (t < 10 * 60)]
    fila["spr_duka_med"] = float(sp.median()) if len(sp) else np.nan
    filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(anio, len(filas))
