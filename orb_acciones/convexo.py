"""Pago convexo por día, barra de entrada (30 min) y dirección, con el recorrido M1 real.

Para cada día y k = 1..11 (entrada a la apertura de la barra k, hora NY desde 9:30), y para largo y corto:
R hasta el cierre (15:59) con stop a 0,15 / 0,30 × ATR14 diario, comprobado vela a vela en M1 (hueco: se
llena a la apertura de la vela). También la horquilla a la entrada y a la salida, en R.
"""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df

sim, d, salida = sys.argv[1:4]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b[["open", "high", "low", "close"]] + a[["open", "high", "low", "close"]]) / 2
m["spr"] = (a.close - b.close).clip(lower=0)
t = m.index.hour * 60 + m.index.minute
m = m[(t >= 570) & (t < 960)]
dias = []
for f, g in m.groupby(m.index.date):
    dias.append((f, g))
hl = pd.DataFrame([(f, g.high.max(), g.low.min(), g.close.iloc[-1]) for f, g in dias], columns=["f", "h", "l", "c"]).set_index("f")
pc = hl.c.shift(1)
atr = pd.concat([hl.h - hl.l, (hl.h - pc).abs(), (hl.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
filas = []
for f, g in dias:
    A = atr.get(f, np.nan)
    if not np.isfinite(A) or len(g) < 380:
        continue
    tt = (g.index.hour * 60 + g.index.minute).values
    O, H, L, S = g.open.values, g.high.values, g.low.values, g.spr.values
    salida_px, salida_spr = g.close.values[-1], S[-1]
    for k in range(1, 12):
        i0 = np.searchsorted(tt, 570 + 30 * k)
        if i0 >= len(tt) or tt[i0] != 570 + 30 * k:
            continue
        ent = O[i0]
        fila = dict(fecha=f, sim=sim, k=k, atr=A, ent=ent)
        for mult in (0.15, 0.30):
            dist = mult * A
            for lado in (1, -1):
                stop = ent - lado * dist
                r, sp = None, salida_spr
                for i in range(i0, len(O)):
                    if (lado == 1 and L[i] <= stop) or (lado == -1 and H[i] >= stop):
                        px = stop if i == i0 else (min(stop, O[i]) if lado == 1 else max(stop, O[i]))
                        r, sp = lado * (px - ent) / dist, S[i]
                        break
                if r is None:
                    r = lado * (salida_px - ent) / dist
                tag = f"{'L' if lado == 1 else 'S'}{int(mult * 100)}"
                fila["r_" + tag] = r
                fila["c_" + tag] = (S[i0] / 2 + sp / 2) / dist
        filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.5g")
print(sim, len(filas))
