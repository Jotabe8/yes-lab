"""Precios por día en horas de la noche de NY (1:00, 4:00) y de la sesión, con horquilla. Uso: noche.py SIM dir año salida"""
import sys, glob, os
import numpy as np, pandas as pd

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close"]]

sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
b, a = cargar(d, "bid"), cargar(d, "ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2
spr = (a.close - b.close).clip(lower=0)
mins = m.index.hour * 60 + m.index.minute
filas = []
for f, g in m.groupby(m.index.date):
    if f.year != anio:
        continue
    t = g.index.hour * 60 + g.index.minute
    s = spr.loc[g.index]
    def px(mi):
        x = np.flatnonzero((t >= mi) & (t < mi + 3))
        return (g.open.iloc[x[0]], s.iloc[x[0]]) if len(x) else (np.nan, np.nan)
    fila = dict(fecha=f, sim=sim)
    for nom, mi in (("p0100", 60), ("p0400", 240), ("p0930", 570), ("p1200", 720), ("p1500", 900), ("p1559", 959)):
        fila[nom], fila["s" + nom[1:]] = px(mi)
    ses = g[(t >= 570) & (t < 960)]
    fila["h"], fila["l"] = (ses.high.max(), ses.low.min()) if len(ses) else (np.nan, np.nan)
    filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
print(sim, anio, len(filas))
