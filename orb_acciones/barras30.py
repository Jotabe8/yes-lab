"""Barras de 30 min (precio medio) y horquilla media por barra de un índice US, hora NY 9:30-16:00."""
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
m["fecha"] = m.index.date
m["bar"] = ((m.index.hour * 60 + m.index.minute) - 570) // 30
g = m.groupby(["fecha", "bar"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"),
                                    spr=("spr", "mean"), n=("open", "size"))
g.reset_index().assign(sim=sim).to_csv(salida, index=False, float_format="%.6g")
print(sim, len(g))
