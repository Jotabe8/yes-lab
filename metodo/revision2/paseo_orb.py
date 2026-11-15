"""Revisión 2 (PREREGISTRO.md, parte A): el motor del ORB GER40 (v3/orb_ger40.py) y del ORB JP225
(v3/orb_asia.py) corrido sobre velas de paseo aleatorio. Las funciones tramo/orb/ATR son copia literal
de esos scripts; lo único nuevo es pasar el precio medio por sinteticos.velas_paseo antes.
Uso: paseo_orb.py SIM dir_velas año n_replicas salida.csv   (SIM = GER40 o JP225)
rep = -1 es la serie real (debe reproducir el resultado de v3)."""
import sys, glob, os
from datetime import date
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from metodo.sinteticos import velas_paseo

sim, d, anio, nrep, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True)
    return df[["open", "high", "low", "close"]]

def tramo(g, lado, ent, dist):
    stop = ent - lado * dist
    lo, hi, op = g.low.values, g.high.values, g.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop: return ((stop if i == 0 else min(stop, op[i])) - ent) / dist
        if lado == -1 and hi[i] >= stop: return (ent - (stop if i == 0 else max(stop, op[i]))) / dist
    return lado * (g.close.values[-1] - ent) / dist

# ------------------------------------------------------------------ GER40 (v3/orb_ger40.py)
def ger40(m):
    srv = m.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
    dd = m.groupby(srv.date).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    pc = dd.c.shift(1)
    atr = pd.concat([dd.h - dd.l, (dd.h - pc).abs(), (dd.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    m = m.copy(); m.index = m.index.tz_convert("Europe/Berlin")
    out = []
    for f, g in m.groupby(m.index.date):
        if f.year != anio or f.weekday() >= 5 or not np.isfinite(atr.get(f, np.nan)): continue
        t = g.index.hour * 60 + g.index.minute; dist = 0.15 * atr[f]; ini = 9 * 60
        rg = g[(t >= ini) & (t < ini + 10)]
        if len(rg) < 7: continue
        O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
        if H - L <= 0 or abs(C - O) < 0.1 * (H - L): continue
        lado = 1 if C > O else -1
        post = g[(t >= ini + 10) & (t < 17 * 60 + 25)]
        if len(post) < 10: continue
        ent = post.open.iloc[0]
        out.append((f, lado, tramo(post, lado, ent, dist), tramo(post, -lado, ent, dist), dist / ent))
    return out

# ------------------------------------------------------------------ JP225 (v3/orb_asia.py)
def jp225(m):
    tz, a0 = "Asia/Tokyo", 9 * 60
    cierre = lambda f: 15 * 60 if f < date(2024, 11, 5) else 15 * 60 + 30
    m = m.copy(); m.index = m.index.tz_convert(tz)
    fechas = m.index.date
    rows = []
    for f, g in m.groupby(fechas):
        t = g.index.hour * 60 + g.index.minute
        s = g[(t >= a0) & (t < cierre(f))]
        if len(s) > 30: rows.append((f, s.high.max(), s.low.min(), s.close.iloc[-1]))
    hl = pd.DataFrame(rows, columns=["f", "h", "l", "c"]).set_index("f")
    pc = hl.c.shift(1)
    atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    out = []
    for f, g in m.groupby(fechas):
        if f.year != anio or g.index[0].weekday() >= 5 or not np.isfinite(atr.get(f, np.nan)): continue
        t = g.index.hour * 60 + g.index.minute; fin = cierre(f); dist = 0.15 * atr[f]
        rg = g[(t >= a0) & (t < a0 + 30)]
        if len(rg) < 20: continue
        O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
        if H - L <= 0 or abs(C - O) < 0.1 * (H - L): continue
        lado = 1 if C > O else -1
        post = g[(t >= a0 + 30) & (t < fin)]
        if len(post) < 10: continue
        ent = post.open.iloc[0]
        out.append((f, lado, tramo(post, lado, ent, dist), tramo(post, -lado, ent, dist), dist / ent))
    return out

b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
mid = (b + a) / 2
mid.index = mid.index.tz_convert({"GER40": "Europe/Berlin", "JP225": "Asia/Tokyo"}[sim])  # barajar por minuto LOCAL
motor = {"GER40": ger40, "JP225": jp225}[sim]
filas = []
for rep in range(-1, nrep):
    v = mid if rep < 0 else velas_paseo(mid, semilla=1000 * anio + rep)
    for f, lado, r, rc, dpct in motor(v):
        filas.append(dict(sim=sim, rep=rep, fecha=f, lado=lado, r=r, r_contra=rc, dist_pct=dpct))
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(sim, anio, len(filas))
