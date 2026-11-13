"""Precios medios y spread por día en horas de Londres alrededor del fix y placebo. Uso: fix.py SIM dir año salida"""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("Europe/London")
    return df[["open", "close"]]

sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b.open + a.open) / 2
spr = (a.open - b.open).clip(lower=0)
HORAS = {"1130": 690, "1200": 720, "1205": 725, "1230": 750, "1300": 780,
         "1530": 930, "1600": 960, "1605": 965, "1630": 990, "1700": 1020}
filas = []
for f, g in m.groupby(m.index.date):
    if f.year != anio or f.weekday() >= 5:
        continue
    t = g.index.hour * 60 + g.index.minute
    s = spr.loc[g.index]
    fila = dict(fecha=f, sim=sim)
    for nom, mi in HORAS.items():
        x = np.flatnonzero((t >= mi) & (t < mi + 3))
        fila["p" + nom], fila["s" + nom] = (g.iloc[x[0]], s.iloc[x[0]]) if len(x) else (np.nan, np.nan)
    filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.7g")
print(sim, anio, len(filas))
