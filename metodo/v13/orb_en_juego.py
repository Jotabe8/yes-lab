"""ORB en juego en aperturas propias (preregistro metodo/v13/PREREGISTRO_ORB_EN_JUEGO.md).
Uso: orb_en_juego.py SIM dir_velas año salida.csv. M1 bid/ask Dukascopy con volumen -> precio medio, hora local."""
import sys, glob, os
from datetime import date
import numpy as np, pandas as pd

MERC = {  # zona, apertura (min locales), salida (min) en función de la fecha
    "GER40": ("Europe/Berlin", 9 * 60, lambda f: 17 * 60 + 25),
    "UK100": ("Europe/London", 8 * 60, lambda f: 16 * 60 + 25),
    "JP225": ("Asia/Tokyo", 9 * 60, lambda f: 14 * 60 + 55 if f < date(2024, 11, 5) else 15 * 60 + 25),
    "XAUUSD": ("America/New_York", 8 * 60 + 20, lambda f: 13 * 60 + 25),
    "USOIL": ("America/New_York", 9 * 60, lambda f: 14 * 60 + 25),
    "US100": ("America/New_York", 9 * 60 + 30, lambda f: 15 * 60 + 55),
}

def cargar(d, lado, tz):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit="ms", utc=True)).tz_convert(tz)
    if "volume" not in df: df["volume"] = np.nan
    return df[["open", "high", "low", "close", "volume"]]

def tramo(g, lado, ent, dist):
    stop = ent - lado * dist
    lo, hi, op = g.low.values, g.high.values, g.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop: return ((stop if i == 0 else min(stop, op[i])) - ent) / dist
        if lado == -1 and hi[i] >= stop: return (ent - (stop if i == 0 else max(stop, op[i]))) / dist
    return lado * (g.close.values[-1] - ent) / dist

if __name__ == "__main__":
    sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    tz, a0, fin = MERC[sim]
    b, a = cargar(d, "bid", tz), cargar(d, "ask", tz)
    idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
    m = (b[["open", "high", "low", "close"]] + a[["open", "high", "low", "close"]]) / 2
    vol = b.volume
    t_all = m.index.hour * 60 + m.index.minute
    fechas = np.array(m.index.date)
    dias = []
    for f, g in m.groupby(fechas):
        if f.weekday() >= 5: continue
        t = g.index.hour * 60 + g.index.minute
        ses = g[(t >= a0) & (t < fin(f))]
        rg = g[(t >= a0) & (t < a0 + 10)]
        if len(ses) < 60 or len(rg) < 7: continue
        v = vol.loc[rg.index]
        dias.append(dict(fecha=f, h=ses.high.max(), l=ses.low.min(), c=ses.close.iloc[-1],
                         rh=rg.high.max(), rl=rg.low.min(), vr=float(v.sum()) if v.notna().any() else np.nan))
    dd = pd.DataFrame(dias).set_index("fecha")
    pc = dd.c.shift(1)
    dd["atr"] = pd.concat([dd.h - dd.l, (dd.h - pc).abs(), (dd.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    dd["rvol"] = dd.vr / dd.vr.rolling(14).mean().shift(1)
    rango = dd.rh - dd.rl
    dd["rrango"] = rango / rango.rolling(14).mean().shift(1)
    filas = []
    for f, g in m.groupby(fechas):
        if f.year != anio or f not in dd.index or not np.isfinite(dd.atr[f]): continue
        t = g.index.hour * 60 + g.index.minute
        dist = 0.15 * dd.atr[f]
        fila = dict(fecha=f, sim=sim, atr=dd.atr[f], dist=dist, rvol=dd.rvol[f], rrango=dd.rrango[f], vr=dd.vr[f])
        rg = g[(t >= a0) & (t < a0 + 10)]
        O, C, H, L = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
        post = g[(t >= a0 + 10) & (t < fin(f))]
        if H - L > 0 and abs(C - O) >= 0.1 * (H - L) and len(post) >= 10:
            lado = 1 if C > O else -1
            ent = post.open.iloc[0]
            fila.update(lado=lado, px=ent, r=tramo(post, lado, ent, dist), r_contra=tramo(post, -lado, ent, dist))
        filas.append(fila)
    pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
    print(sim, anio, len(filas))
