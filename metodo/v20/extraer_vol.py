"""v20: volumen M1 de Dukascopy (lado bid, -v) -> matriz días x minutos de sesión. Uso: extraer_vol.py SIM dir año salida.npz"""
import sys, glob, os
import numpy as np, pandas as pd
SES = {"US100": ("America/New_York", 570, 960), "US500": ("America/New_York", 570, 960),
       "US30": ("America/New_York", 570, 960), "GER40": ("Europe/Berlin", 540, 1050)}
sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
tz, A, C = SES[sim]
fs = [f for f in sorted(glob.glob(f"{d}/*.csv")) if os.path.getsize(f) > 0]
df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
print(df.columns.tolist(), df.head(2).to_dict("records"))
df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert(tz)
df = df[df.index.year == anio]
t = df.index.hour * 60 + df.index.minute
df = df[(t >= A) & (t < C) & (df.index.dayofweek < 5)]
n = C - A; fechas, arr = [], []
for f, g in df.groupby(df.index.date):
    v = np.full(n, np.nan, np.float32)
    k = (g.index.hour * 60 + g.index.minute).values - A
    v[k] = g["volume"].values
    fechas.append(str(f)); arr.append(v)
np.savez_compressed(salida, fechas=np.array(fechas), v=np.array(arr))
print(sim, anio, len(fechas))
