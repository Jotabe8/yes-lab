"""ORB de la apertura propia en Asia (preregistro metodo/v3/PREREGISTRO_ORB_ASIA.md).
Uso: orb_asia.py SIM dir_velas año salida.csv. M1 bid/ask Dukascopy -> precio medio, hora local del mercado."""
import sys, glob, os
from datetime import date
import numpy as np, pandas as pd

MERC = {  # zona, apertura (min), cierre (min) -> función de la fecha
    "JP225": ("Asia/Tokyo", 9 * 60, lambda f: 15 * 60 if f < date(2024, 11, 5) else 15 * 60 + 30),
    "HK50": ("Asia/Hong_Kong", 9 * 60 + 30, lambda f: 16 * 60),
    "AUS200": ("Australia/Sydney", 10 * 60, lambda f: 16 * 60),
}

def cargar(d, lado, tz):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert(tz)
    return df[["open", "high", "low", "close"]]

def tramo(g, lado, ent, dist):
    stop = ent - lado * dist
    lo, hi, op = g.low.values, g.high.values, g.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop: return ((stop if i == 0 else min(stop, op[i])) - ent) / dist
        if lado == -1 and hi[i] >= stop: return (ent - (stop if i == 0 else max(stop, op[i]))) / dist
    return lado * (g.close.values[-1] - ent) / dist

sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
tz, a0, cierre = MERC[sim]
b, a = cargar(d, "bid", tz), cargar(d, "ask", tz)
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2; spr = (a.close - b.close)
mins = m.index.hour * 60 + m.index.minute
fechas = pd.Series(m.index.date, index=m.index)
# rangos diarios de sesión para el ATR
rows = []
for f, g in m.groupby(fechas.values):
    t = g.index.hour * 60 + g.index.minute
    s = g[(t >= a0) & (t < cierre(f))]
    if len(s) > 30: rows.append((f, s.high.max(), s.low.min(), s.close.iloc[-1]))
hl = pd.DataFrame(rows, columns=["f", "h", "l", "c"]).set_index("f")
pc = hl.c.shift(1)
atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)

def orb(g, t, ini, fin, dist):
    rg = g[(t >= ini) & (t < ini + 30)]
    if len(rg) < 20: return None
    O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
    if H - L <= 0 or abs(C - O) < 0.1 * (H - L): return None
    lado = 1 if C > O else -1
    post = g[(t >= ini + 30) & (t < fin)]
    if len(post) < 10: return None
    ent = post.open.iloc[0]
    d30 = 2 * dist; dext = max(H - L, dist / 1.5)          # dist = 0,15 ATR -> 0,30 ATR y mínimo 0,10 ATR
    return (lado, tramo(post, lado, ent, dist), tramo(post, -lado, ent, dist), ent,
            tramo(post, lado, ent, d30), tramo(post, -lado, ent, d30), tramo(post, lado, ent, dext), tramo(post, -lado, ent, dext), dext)

filas = []
for f, g in m.groupby(fechas.values):
    if f.year != anio or g.index[0].weekday() >= 5 or not np.isfinite(atr.get(f, np.nan)): continue
    t = g.index.hour * 60 + g.index.minute
    fin = cierre(f); dist = 0.15 * atr[f]
    fila = dict(fecha=f, sim=sim, atr=atr[f], dist=dist)
    x = orb(g, t, a0, fin, dist)
    if x: fila.update(lado=x[0], r=x[1], r_contra=x[2], px=x[3], r_s30=x[4], c_s30=x[5], r_ext=x[6], c_ext=x[7], dist_ext=x[8])
    y = orb(g, t, a0 + 120, fin, dist)
    if y: fila.update(r_hora=y[1], r_hora_contra=y[2])
    sp = spr.loc[g.index][(t >= a0) & (t < a0 + 60)]
    fila["spr_duka_med"] = float(sp.median()) if len(sp) else np.nan
    filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(sim, anio, len(filas))
