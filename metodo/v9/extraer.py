"""Extrae de M1 Dukascopy bid/ask (precio medio) la ventana 07:00-16:59 NY de cada día laborable
y las velas diarias (corte 17:00 NY). Uso: python extraer.py SIM dir_velas salida_prefijo"""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close"]]

sim, d, sal = sys.argv[1:4]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2
m["spr"] = (a.close - b.close).clip(lower=0)
# diario con corte 17:00 NY
dd = m.copy(); dd["dia"] = (dd.index + pd.Timedelta(hours=7)).date
g = dd.groupby("dia").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), n=("open", "size"))
g.to_csv(f"{sal}_diario.csv")
# ventana intradía
t = m.index.hour * 60 + m.index.minute
w = m[(t >= 420) & (t < 1020) & (m.index.dayofweek < 5)].copy()
w["fecha"] = w.index.date; w["k"] = (w.index.hour * 60 + w.index.minute) - 420
fechas = np.array(sorted(w.fecha.unique()))
pos = {f: i for i, f in enumerate(fechas)}
arr = np.full((len(fechas), 600, 5), np.nan, np.float32)
fi = w.fecha.map(pos).values; ki = w.k.values
for j, c in enumerate(["open", "high", "low", "close", "spr"]):
    arr[fi, ki, j] = w[c].values
np.savez_compressed(f"{sal}_m1.npz", fechas=np.array([str(f) for f in fechas]), x=arr)
print(sim, len(fechas), len(g))
