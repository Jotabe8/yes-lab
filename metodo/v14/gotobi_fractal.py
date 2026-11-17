"""Gotobi + Hurst por día (PREREGISTRO_DESCARTADOS.md). Uso: gotobi_fractal.py SIM dir_velas año salida.csv
Para TODOS los días hábiles: resultado de comprar 08:00 JST y cerrar 09:55, bandera gotobi, H5 y Hhoy."""
import sys, glob, os, calendar
from datetime import date, timedelta
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractales import hurst_dfa, E5, EH

TZ = "Asia/Tokyo"; ENT, SAL = 8 * 60, 9 * 60 + 55

def dias_gotobi(anio):
    out = set()
    for m in range(1, 13):
        ult = calendar.monthrange(anio, m)[1]
        for d in [5, 10, 15, 20, 25, ult]:
            f = date(anio, m, d)
            while f.weekday() >= 5: f -= timedelta(days=1)
            out.add(f)
    return out

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit="ms", utc=True)).tz_convert(TZ)
    return df[["open", "high", "low", "close"]]

if __name__ == "__main__":
    sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    b, a = cargar(d, "bid"), cargar(d, "ask")
    idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
    mid = (b.close + a.close) / 2
    lp = np.log(mid.values); tmin = np.asarray(idx.hour * 60 + idx.minute)
    k = np.asarray(idx.year * 10000 + idx.month * 100 + idx.day)
    got = dias_gotobi(anio) | dias_gotobi(anio - 1)
    info = {}
    for kk in pd.unique(k):
        f = date(int(kk) // 10000, int(kk) // 100 % 100, int(kk) % 100)
        if f.weekday() >= 5: continue
        lo, hi = np.searchsorted(k, kk, "left"), np.searchsorted(k, kk, "right")
        info[f] = (lo, hi)
    dias = sorted(info)
    rng_d = {f: float(b.high.values[info[f][0]:info[f][1]].max() - b.low.values[info[f][0]:info[f][1]].min()) for f in dias}
    ses = {}
    for f in dias:
        lo, hi = info[f]; ii = np.arange(lo, hi)[tmin[lo:hi] < SAL]
        if len(ii) >= 60: ses[f] = np.diff(lp[ii])
    filas = []
    for i, f in enumerate(dias):
        if f.year != anio or i < 14: continue
        lo, hi = info[f]
        t = tmin[lo:hi]; ii = np.arange(lo, hi)
        tramo = ii[(t >= ENT) & (t < SAL)]
        if len(tramo) < 60 or tramo[0] != ii[t >= ENT][0] or tmin[tramo[0]] != ENT: continue
        adr = np.mean([rng_d[g] for g in dias[i - 14:i]])
        dist = 0.25 * adr
        ent = a.open.values[tramo[0]]; stop = ent - dist
        lo_b, op_b = b.low.values[tramo], b.open.values[tramo]
        r = (b.close.values[tramo[-1]] - ent) / dist
        for j in range(len(tramo)):
            if lo_b[j] <= stop:
                r = ((stop if j == 0 else min(stop, op_b[j])) - ent) / dist; break
        fila = dict(fecha=f, sim=sim, gotobi=int(f in got), r=r, dist=dist, px=ent)
        prev = [g for g in dias[max(0, i - 10):i] if g in ses][-5:]
        if len(prev) == 5:
            fila["h5"] = hurst_dfa(np.concatenate([ses[g] for g in prev]), E5)
        j0 = tramo[0]
        if j0 >= 391: fila["hhoy"] = hurst_dfa(np.diff(lp[j0 - 391:j0]), EH)
        filas.append(fila)
    pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.6g")
    print(sim, anio, len(filas), sum(x["gotobi"] for x in filas))
