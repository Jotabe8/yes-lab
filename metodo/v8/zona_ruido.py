"""Zona de ruido (Zarattini, Aziz, Barbon 2024) en índices europeos. Preregistro: metodo/v8/PREREGISTRO_ZONA_RUIDO.md
Uso: zona_ruido.py dir_velas MERCADO año salida_dias.csv salida_ops.csv
M1 bid/ask Dukascopy -> precio medio, hora local de la bolsa."""
import sys, glob, os
import numpy as np, pandas as pd

MERC = {  # zona horaria, apertura (min), cierre forzado (min), fin de sesión (min)
    "GER40": ("Europe/Berlin", 9 * 60, 17 * 60 + 25, 17 * 60 + 30),
    "UK100": ("Europe/London", 8 * 60, 16 * 60 + 25, 16 * 60 + 30),
    "EU50": ("Europe/Berlin", 9 * 60, 17 * 60 + 25, 17 * 60 + 30),
}

def cargar(d, lado):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True)
    cols = ["open", "high", "low", "close"] + (["volume"] if "volume" in df else [])
    return df[cols]

def sesion(d, mercado):
    tz, ap, cf, fin = MERC[mercado]
    b, a = cargar(d, "bid"), cargar(d, "ask")
    idx = b.index.intersection(a.index); b, a = b.loc[idx], a.loc[idx]
    m = (b[["open", "high", "low", "close"]] + a[["open", "high", "low", "close"]]) / 2
    m["vol"] = (b["volume"] + a["volume"]) if "volume" in b and "volume" in a else 1.0
    m.index = m.index.tz_convert(tz)
    t = m.index.hour * 60 + m.index.minute
    m = m[(t >= ap) & (t < fin)]
    m["k"] = (m.index.hour * 60 + m.index.minute) - ap
    m["f"] = m.index.date
    return m, ap, cf, fin

def simular(dia, sig, O, pc, kcierre, signo=1, desfase=0, coste=0.0):
    """dia: DataFrame por minuto k (índice k). Devuelve lista de operaciones (lado, entrada, salida, ret)."""
    c = dia.close; tp = (dia.high + dia.low + dia.close) / 3
    w = dia.vol.where(dia.vol > 0, 1.0)
    vwap = (tp * w).cumsum() / w.cumsum()
    ub = max(O, pc) * (1 + sig); lb = min(O, pc) * (1 - sig)
    pos, ent, kent, ops = 0, 0.0, 0, []
    decis = [k for k in range(30 + desfase, kcierre, 30)]
    for k in decis + [kcierre]:
        kk = k - 1  # precio al cierre de la vela anterior = precio en el instante k
        if kk not in c.index: continue
        P = c[kk]
        if k == kcierre:
            if pos: ops.append((pos, kent, k, pos * (P / ent - 1) - coste))
            break
        u, l, v = ub.get(kk, np.nan), lb.get(kk, np.nan), vwap[kk]
        if not np.isfinite(u): continue
        if signo == 1: dese = 1 if P > max(u, v) else (-1 if P < min(l, v) else 0)
        else: dese = -1 if P > u else (1 if P < l else 0)
        if signo == 1 and pos == 1 and P <= max(u, v): salir = True
        elif signo == 1 and pos == -1 and P >= min(l, v): salir = True
        elif signo == -1 and pos != 0 and l <= P <= u: salir = True
        else: salir = False
        if pos and (salir or (dese and dese != pos)):
            ops.append((pos, kent, k, pos * (P / ent - 1) - coste)); pos = 0
        if pos == 0 and dese:
            pos, ent, kent = dese, P, k
    return ops

if __name__ == "__main__":
    d, mercado, anio, sal_d, sal_o = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    m, ap, cf, fin = sesion(d, mercado)
    kcierre = cf - ap
    dias = []
    for f, g in m.groupby("f"):
        g = g.drop_duplicates("k").set_index("k")
        if f.weekday() >= 5 or len(g) < 0.8 * (fin - ap): continue
        dias.append((f, g))
    fd, od = [], []
    for i in range(15, len(dias)):
        f, g = dias[i]
        if f.year != anio: continue
        O = g.open.iloc[0]; pc = dias[i - 1][1].close.iloc[-1]
        prev = [dd for _, dd in dias[i - 14:i]]
        mov = pd.concat([(dd.close / dd.open.iloc[0] - 1).abs() for dd in prev], axis=1).mean(axis=1)
        # vol diaria (14 sesiones, rentabilidad apertura-cierre) para normalizar a "R"
        rd = np.array([dd.close.iloc[-1] / dd.open.iloc[0] - 1 for dd in prev]); sd = rd.std(ddof=1)
        fila = dict(fecha=f, sd14=sd)
        for nom, sg, des in [("base", 1, 0), ("contra", -1, 0), ("hora15", 1, 15)]:
            ops = simular(g, mov, O, pc, kcierre, sg, des)
            fila[f"r_{nom}"] = sum(o[3] for o in ops); fila[f"n_{nom}"] = len(ops)
            if nom == "base":
                for o in ops: od.append(dict(fecha=f, lado=o[0], k_ent=o[1], k_sal=o[2], ret=o[3]))
        fd.append(fila)
    pd.DataFrame(fd).to_csv(sal_d, index=False, float_format="%.6g")
    pd.DataFrame(od).to_csv(sal_o, index=False, float_format="%.6g")
    print(mercado, anio, len(fd), "días", len(od), "ops")
