"""v15: M1 bid/ask Dukascopy -> precio medio de sesión en matrices días x minutos (npz). Uso: extraer.py SIM dir año salida.npz"""
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
m = m[m.index.year == anio]
t = m.index.hour * 60 + m.index.minute
m = m[(t >= A) & (t < C)]
n = C - A; fechas = []; arr = []
for f, g in m.groupby(m.index.date):
    if len(g) < 0.8 * n or g.index[0].weekday() >= 5: continue
    x = np.full((n, 4), np.nan, np.float32)
    k = (g.index.hour * 60 + g.index.minute).values - A
    x[k] = g[["open", "high", "low", "close"]].values
    fechas.append(str(f)); arr.append(x)
np.savez_compressed(salida, fechas=np.array(fechas), x=np.array(arr))
print(sim, anio, len(fechas))
