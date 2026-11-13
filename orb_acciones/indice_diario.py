"""Precios clave por día de un índice desde M1 bid/ask Dukascopy (hora NY): 9:30, 9:35, 15:55, H/L/C de sesión."""
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
filas = []
for f, g in m.groupby(m.index.date):
    tt = g.index.hour * 60 + g.index.minute
    def px(mi):
        x = g[tt == mi]
        return (x.open.iloc[0], x.spr.iloc[0]) if len(x) else (np.nan, np.nan)
    (o, so), (p5, s5), (p55, s55) = px(570), px(575), px(955)
    filas.append(dict(fecha=f, sim=sim, o930=o, p935=p5, s935=s5, p1555=p55, s1555=s55,
                      h=g.high.max(), l=g.low.min(), c=g.close.iloc[-1]))
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(sim, len(filas))
