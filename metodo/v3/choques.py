"""Reversión tras choques de 5 min (PREREGISTRO_CHOQUES.md). Uso: choques.py SIM dir año salida.csv"""
import sys, glob, os
import numpy as np, pandas as pd
SES = {"US100": ("America/New_York", 570, 960), "US500": ("America/New_York", 570, 960),
       "US30": ("America/New_York", 570, 960), "GER40": ("Europe/Berlin", 540, 1050)}
sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
tz, A, C = SES[sim]
def cargar(lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert(tz)
    return df[["open", "high", "low", "close"]]
b, a = cargar("bid"), cargar("ask"); idx = b.index.intersection(a.index)
m = (b.loc[idx] + a.loc[idx]) / 2
t = m.index.hour * 60 + m.index.minute
m = m[(t >= A) & (t < C)]
dias = [(f, g) for f, g in m.groupby(m.index.date) if len(g) > 0.8 * (C - A) and g.index[0].weekday() < 5]
# sigma de 5 min de las 20 sesiones anteriores (rendimientos no solapados)
sig = {}
r5d = {f: np.diff(np.log(g.close.values[::5])) for f, g in dias}
fechas = [f for f, _ in dias]
for i, f in enumerate(fechas):
    if i >= 20: sig[f] = np.std(np.concatenate([r5d[x] for x in fechas[i - 20:i]]))

def tramo(o, h, l, c, i0, lado, ent, dist, n):
    stop = ent - lado * dist
    for j in range(i0, min(i0 + n, len(c))):
        if lado == 1 and l[j] <= stop: return ((stop if j == i0 else min(stop, o[j])) - ent) / dist
        if lado == -1 and h[j] >= stop: return (ent - (stop if j == i0 else max(stop, o[j]))) / dist
    j = min(i0 + n, len(c)) - 1
    return lado * (c[j] - ent) / dist

filas = []; prev = None
for f, g in dias:
    if f.year != anio or f not in sig:
        prev = g; continue
    o, h, l, c = g.open.values, g.high.values, g.low.values, g.close.values
    mins = (g.index.hour * 60 + g.index.minute).values
    lc = np.log(c); s = sig[f]; libre = 0
    for i in range(5, len(c) - 1):
        if mins[i] < A + 15 or mins[i] > C - 46 or i < libre: continue
        r5 = lc[i] - lc[i - 5]; z = abs(r5) / s if s > 0 else 0
        if z < 3: continue
        lado = -int(np.sign(r5)); dist = abs(c[i] - c[i - 5]); ent = o[i + 1]
        fila = dict(fecha=f, hora=int(mins[i]), sim=sim, z=z, px=ent, dist=dist,
                    r30=tramo(o, h, l, c, i + 1, lado, ent, dist, 30), r60=tramo(o, h, l, c, i + 1, lado, ent, dist, 60),
                    seguir30=tramo(o, h, l, c, i + 1, -lado, ent, dist, 30))
        if prev is not None:   # placebo: misma hora del día anterior, mismo stop, en contra de sus 5 min previos
            pm = (prev.index.hour * 60 + prev.index.minute).values; k = np.where(pm == mins[i])[0]
            if len(k) and 5 <= k[0] < len(prev) - 1:
                pc = prev.close.values; po, ph, pl = prev.open.values, prev.high.values, prev.low.values; k = k[0]
                ld = -int(np.sign(pc[k] - pc[k - 5]) or 1)
                fila["placebo30"] = tramo(po, ph, pl, pc, k + 1, ld, po[k + 1], dist, 30)
        filas.append(fila); libre = i + 31
    prev = g
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(sim, anio, len(filas))
