"""Extrae de las velas M1 bid/ask de Dukascopy (un año) lo que necesitan las re-pruebas:
   - ventana M1 en precio medio + horquilla (gotobi: 22:55-01:00 UTC; eia: 10:25-14:35 NY, días laborables)
   - velas diarias de servidor (NY 17:00) en precio medio para el stop por ATR.
Uso: extraer.py SIM dir_velas año tipo(gotobi|eia) carpeta_salida"""
import sys, glob, os
import numpy as np, pandas as pd

sim, d, anio, tipo, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]

def cargar(lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True)
    return df[["open", "high", "low", "close"]]

b, a = cargar("bid"), cargar("ask")
idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b + a) / 2
m["spread"] = (a.open - b.open).clip(lower=0)
ny = m.index.tz_convert("America/New_York")
# día de servidor = hora NY + 7 h
dia_srv = (ny + pd.Timedelta(hours=7)).date
d1 = m.groupby(dia_srv).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("open", "size"))
d1 = d1[[x.year == anio for x in d1.index]]
d1 = d1[d1.n >= 60]
d1.index.name = "dia"
os.makedirs(out, exist_ok=True)
d1.to_csv(f"{out}/{sim}_{anio}_d1.csv", float_format="%.7g")

if tipo == "gotobi":
    mi = m.index.hour * 60 + m.index.minute
    sel = ((mi >= 22 * 60 + 55) | (mi < 60)) & (m.index.year == anio)
else:
    mi = ny.hour * 60 + ny.minute
    sel = (mi >= 10 * 60 + 25) & (mi <= 14 * 60 + 35) & (ny.dayofweek < 5) & (ny.year == anio)
w = m[sel].copy()
w.insert(0, "ts", ((w.index - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1min")).astype(np.int64))  # minutos UTC
w.to_csv(f"{out}/{sim}_{anio}_m1.csv.gz", index=False, float_format="%.7g")
print(sim, anio, tipo, "m1", len(w), "d1", len(d1))
