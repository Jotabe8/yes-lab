"""v3 / candidato 1: ORB cripto simulado sobre el PRECIO MEDIO (como un futuro de CME con 1 tick de horquilla).
El original entraba a ask y comprobaba el stop en bid: con la horquilla de Dukascopy (0,2-6 R) el bruto
reconstruido como r + spr era un artefacto. Aquí todo va en medio; los costes se aplican después.

Variantes del ORB (mismo mecanismo) por día. Uso: orb_variantes.py SIM dir año salida.csv
Rango 9:30-9:30+L (L = 5, 10, 15, 30, 60 min), dirección de la vela del rango (cuerpo >= 10 %), entrada al
final del rango a ask/bid, stop 15 % ATR14, salida 15:55. Para L=10 además 'SAR': tras saltar el stop, entra
en contra (una vez) con el mismo tamaño de stop hasta 15:55. Stop vela a vela en M1 con el lado correcto."""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close"]]

def tramo(bb, aa, lado, ent, dist):
    """Devuelve (r, i_salida o None)"""
    stop = ent - lado * dist
    lo, hi, ob, oa = bb.low.values, aa.high.values, bb.open.values, aa.open.values
    for i in range(len(lo)):
        if lado == 1 and lo[i] <= stop:
            px = stop if i == 0 else min(stop, ob[i]); return (px - ent) / dist, i
        if lado == -1 and hi[i] >= stop:
            px = stop if i == 0 else max(stop, oa[i]); return (ent - px) / dist, i
    px = ob[-1] if lado == 1 else oa[-1]
    return lado * (px - ent) / dist, None

sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2
t = m.index.hour * 60 + m.index.minute
ses = (t >= 570) & (t < 960)
dias = {f: g for f, g in m[ses].groupby(m[ses].index.date)}
hl = pd.DataFrame([(f, g.high.max(), g.low.min(), g.close.iloc[-1]) for f, g in dias.items()], columns=["f", "h", "l", "c"]).set_index("f")
pc = hl.c.shift(1)
atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
filas = []
for f, g in dias.items():
    if f.year != anio or not np.isfinite(atr.get(f, np.nan)):
        continue
    tt = g.index.hour * 60 + g.index.minute
    if tt[0] != 570 or (tt == 955).sum() == 0:
        continue
    dist = 0.15 * atr[f]
    fila = dict(fecha=f, sim=sim, atr=atr[f], px=float(g.open.iloc[0]))
    for L in (5, 10, 15, 30, 60):
        rg = g[tt < 570 + L]
        O, C, H, Lo = rg.open.iloc[0], rg.close.iloc[-1], rg.high.max(), rg.low.min()
        if len(rg) < 0.8 * L or H - Lo <= 0 or abs(C - O) < 0.10 * (H - Lo):
            continue
        lado = 1 if C > O else -1
        post = g.index[(tt >= 570 + L) & (tt <= 955)]
        bb, aa = m.loc[post], m.loc[post]
        ent = aa.open.iloc[0] if lado == 1 else bb.open.iloc[0]
        r, i = tramo(bb, aa, lado, ent, dist)
        fila[f"r{L}"], fila[f"lado{L}"] = r, lado
        fila[f"spr{L}"] = float(a.loc[post].open.iloc[0] - b.loc[post].open.iloc[0]) / dist
        e_c = aa.open.iloc[0] if -lado == 1 else bb.open.iloc[0]
        fila[f"c{L}"], _ = tramo(bb, aa, -lado, e_c, dist)  # placebo: mismo momento y salidas, lado contrario
        if L == 10:
            fila["sar"] = np.nan
            if i is not None and i + 1 < len(post) - 1:
                b2, a2 = bb.iloc[i + 1:], aa.iloc[i + 1:]
                e2 = a2.open.iloc[0] if -lado == 1 else b2.open.iloc[0]
                fila["sar"], _ = tramo(b2, a2, -lado, e2, dist)
                fila["spr_sar"] = np.nan
    filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.5g")
print(sim, anio, len(filas))
