"""v9-A: ruptura en el instante del dato programado (ver PREREGISTRO_EVENTOS.md)."""
import glob, sys
import numpy as np, pandas as pd

D = "datos"
MERCADOS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US100", "US500"]
COMISION = {"XAUUSD": 0.3e-4, "EURUSD": 0.5e-4, "GBPUSD": 0.5e-4, "USDJPY": 0.5e-4, "US100": 0.0, "US500": 0.0}
HORA = {"08:30": 90, "14:00": 420}   # minuto desde las 07:00 NY
FIN = 595                            # 16:55 NY


def cargar(sim):
    fs = sorted(glob.glob(f"{D}/{sim}_*_m1.npz"))
    fe, xs = [], []
    for f in fs:
        z = np.load(f); fe.append(z["fechas"]); xs.append(z["x"])
    fe = np.concatenate(fe); x = np.concatenate(xs)
    _, i = np.unique(fe, return_index=True); fe, x = fe[i], x[i]
    di = pd.concat([pd.read_csv(f, index_col=0) for f in sorted(glob.glob(f"{D}/{sim}_*_diario.csv"))])
    di = di[~di.index.duplicated()].sort_index(); di = di[di.n > 300]
    tr = pd.concat([di.h - di.l, (di.h - di.c.shift()).abs(), (di.l - di.c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)          # solo días anteriores
    atr.index = atr.index.astype(str)
    return fe, x, atr.reindex(fe).values


def operar(x, atr, T, salida, k_stop, comision, lado=1, ver=5):
    """Una operación por día del array x[día, minuto, (o,h,l,c,spr)] en el minuto T."""
    n = len(x); rb = np.full(n, np.nan); co = np.full(n, np.nan)
    fin = min(T + salida, FIN)
    for d in range(n):
        o, c5, e, se = x[d, T, 0], x[d, T + ver - 1, 3], x[d, T + ver, 0], x[d, T + ver, 4]
        if not np.isfinite([o, c5, e, se, atr[d]]).all() or c5 == o or atr[d] <= 0:
            continue
        s = np.sign(c5 - o) * lado; dist = k_stop * atr[d]; stop = e - s * dist
        px, sx = np.nan, np.nan
        for m in range(T + ver, fin):
            mo, mh, ml = x[d, m, 0], x[d, m, 1], x[d, m, 2]
            if not np.isfinite(mo):
                continue
            if s > 0 and mo <= stop: px, sx = mo, x[d, m, 4]; break
            if s < 0 and mo >= stop: px, sx = mo, x[d, m, 4]; break
            if s > 0 and ml <= stop: px, sx = stop, x[d, m, 4]; break
            if s < 0 and mh >= stop: px, sx = stop, x[d, m, 4]; break
        if not np.isfinite(px):
            seg = x[d, fin:fin + 5, 0]; ok = np.isfinite(seg)
            if ok.any():
                j = np.argmax(ok); px, sx = seg[j], x[d, fin + j, 4]
            else:
                cc = x[d, T + ver:fin, 3]; ok = np.isfinite(cc)
                if not ok.any(): continue
                j = np.where(ok)[0][-1]; px, sx = cc[j], x[d, T + ver + j, 4]
        if not np.isfinite(sx): sx = se
        rb[d] = s * (px - e) / dist
        co[d] = (se / 2 + sx / 2 + comision * e) / dist
    return rb, co


def tabla(ev, k_stop=0.15, salida=180, lado=1, dias=None):
    """Devuelve operaciones de todos los mercados. dias: 'evento' o 'placebo'."""
    filas = []
    for sim in MERCADOS:
        fe, x, atr = cargar(sim)
        fd = pd.to_datetime(fe)
        for hora, T in HORA.items():
            tipos = ev[ev.hora == hora]
            esd = set(tipos.fecha)
            if dias == "placebo":
                sel = np.array([(f not in esd) and (f not in set(ev.fecha)) for f in fe])
                if hora == "14:00": sel &= fd >= "2013-01-01"
            else:
                sel = np.isin(fe, list(esd))
            idx = np.where(sel)[0]
            rb, co = operar(x[idx], atr[idx], T, salida, k_stop, COMISION[sim], lado)
            tipo = dict(zip(tipos.fecha, tipos.evento))
            for i, r, c in zip(idx, rb, co):
                if np.isfinite(r):
                    filas.append((fe[i], sim, tipo.get(fe[i], "placebo_" + hora), r, c))
    return pd.DataFrame(filas, columns=["fecha", "sim", "evento", "rb", "coste"])


def t_dia(o, col="neto"):
    g = o.groupby("fecha")[col].mean()
    return g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g)), len(g)


def paseo(x, semilla=0):
    """Paseo aleatorio: baraja entre días las velas de cada minuto (forma relativa a su apertura y
    rendimiento desde el cierre anterior, centrado en 0). Conserva horario y horquilla."""
    rng = np.random.default_rng(semilla)
    n, M, _ = x.shape
    o, h, l, c, sp = (x[:, :, j].astype(float) for j in range(5))
    prev = np.concatenate([o[:, :1], c[:, :-1]], axis=1)
    g = np.log(o / prev); ho, lo, cl = np.log(h / o), np.log(l / o), np.log(c / o)
    y = np.full_like(x, np.nan)
    for m in range(M):
        p = rng.permutation(n)
        for arr in (g, ho, lo, cl, sp):
            arr[:, m] = arr[p, m]
    ret = np.nan_to_num(g) + np.nan_to_num(cl)
    ret = ret - np.nanmean(np.where(np.isfinite(g), ret, np.nan), axis=0)   # martingala por minuto
    base = np.nanmedian(o[:, 0])
    cc = base * np.exp(np.cumsum(ret, axis=1)); oo = cc / np.exp(np.nan_to_num(cl))
    y[:, :, 0] = oo; y[:, :, 1] = oo * np.exp(np.nan_to_num(ho)); y[:, :, 2] = oo * np.exp(np.nan_to_num(lo))
    y[:, :, 3] = cc; y[:, :, 4] = np.nan_to_num(sp)
    return y.astype(np.float32)
