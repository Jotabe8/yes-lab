"""v20: volumen de ticks M1 de FTMO (export MT5, hora servidor = NY+7) -> datos/vol_US100_ftmo.npz (sesión 9:30-16:00 NY)."""
import sys
import numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1])
t = pd.to_datetime(df.time) - pd.Timedelta(hours=7)
df.index = t
m = t.dt.hour * 60 + t.dt.minute
df = df[((m >= 570) & (m < 960)).values & (t.dt.dayofweek < 5).values]
F, V = [], []
for f, g in df.groupby(df.index.date):
    if len(g) < 300:
        continue
    v = np.full(390, np.nan); k = (g.index.hour * 60 + g.index.minute).values - 570
    v[k] = g.tick_volume.values; F.append(str(f)); V.append(v)
np.savez_compressed("datos/vol_US100_ftmo.npz", fechas=np.array(F), v=np.array(V, np.float32))
print(len(F), F[0], F[-1])
