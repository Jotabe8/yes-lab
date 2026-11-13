"""Eventos en niveles redondos vs placebo. Uso: redondos.py SIM dir año salida.csv"""
import sys, glob, os
import numpy as np, pandas as pd
PASO = {"US100": 100.0, "US500": 25.0, "US30": 250.0}
def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close"]]
sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
b, a = cargar(d, "bid"), cargar(d, "ask"); idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
m = (b.close + a.close) / 2
paso = PASO[sim]; filas = []
for f, g in m.groupby(m.index.date):
    if f.year != anio: continue
    t = g.index.hour * 60 + g.index.minute
    ses = (t >= 585) & (t <= 930)
    if ses.sum() < 300: continue
    px = g.values; ix = g.index
    ab, aa = b.close.loc[ix].values, a.close.loc[ix].values
    usados = set()
    for i in np.flatnonzero(ses)[1:]:
        if i + 30 >= len(px): break
        for tipo_nivel, off in (("real", 0.0), ("placebo", paso / 2)):
            # nivel más cercano de este tipo
            n = np.round((px[i] - off) / paso) * paso + off
            dist = (px[i] - n) / n * 1e4
            for ev in ("cruce", "toque"):
                clave = (ev, tipo_nivel, n)
                if clave in usados: continue
                if ev == "cruce":
                    lado_prev = np.sign((px[max(0, i - 15):i] - n)).min() if dist > 0 else -np.sign((px[max(0, i - 15):i] - n)).max()
                    cond = abs(dist) >= 3 and lado_prev < 0  # en los 15 min previos estuvo al otro lado
                    s = np.sign(dist)
                else:
                    lejos = np.abs((px[max(0, i - 30):i] - n) / n * 1e4).min() > 10 if i >= 30 else False
                    cond = abs(dist) <= 1 and lejos
                    s = np.sign(px[i - 1] - n)  # rebote: si llega desde arriba, largo; desde abajo, corto
                if not cond or s == 0: continue
                usados.add(clave)
                ent = aa[i] if s > 0 else ab[i]
                fila = dict(fecha=f, sim=sim, ev=ev, nivel=tipo_nivel, min=int(t[i]), lado=int(s))
                for h in (15, 30):
                    sal = ab[i + h] if s > 0 else aa[i + h]
                    fila[f"r{h}"] = s * (sal - ent) / ent * 1e4
                    fila[f"b{h}"] = s * (px[i + h] - px[i]) / px[i] * 1e4
                filas.append(fila)
pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.4g")
print(sim, anio, len(filas))
