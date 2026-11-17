"""Medidas fractales por día (preregistro metodo/v14/PREREGISTRO_FRACTALES.md).
Uso: fractales.py SIM dir_velas año salida.csv   |   fractales.py prueba  (comprueba el estimador)
Solo usa datos anteriores a la entrada (minuto 10 de la sesión propia)."""
import sys, glob, os
from datetime import date
import numpy as np, pandas as pd

MERC = {  # igual que metodo/v13/orb_en_juego.py
    "GER40": ("Europe/Berlin", 9 * 60, lambda f: 17 * 60 + 25),
    "UK100": ("Europe/London", 8 * 60, lambda f: 16 * 60 + 25),
    "JP225": ("Asia/Tokyo", 9 * 60, lambda f: 14 * 60 + 55 if f < date(2024, 11, 5) else 15 * 60 + 25),
    "XAUUSD": ("America/New_York", 8 * 60 + 20, lambda f: 13 * 60 + 25),
    "US100": ("America/New_York", 9 * 60 + 30, lambda f: 15 * 60 + 55),
}
E5 = np.array([4, 6, 8, 12, 16, 24, 32, 48, 64])
EH = np.array([4, 6, 8, 12, 16, 24, 32])

def _fluct(y, s, q=None):
    """F_q(s) de DFA-1 sobre el perfil y (segmentos no solapados desde el inicio y desde el final)."""
    n = len(y) // s
    if n < 4: return np.nan
    segs = np.concatenate([y[: n * s].reshape(n, s), y[len(y) - n * s:].reshape(n, s)])
    x = np.arange(s) - (s - 1) / 2
    b = segs @ x / (x @ x); a = segs.mean(1, keepdims=True)
    f2 = ((segs - a - b[:, None] * x) ** 2).mean(1)
    f2 = f2[f2 > 0]
    if len(f2) < 4: return np.nan
    if q is None or q == 2: return np.sqrt(f2.mean())
    return (np.mean(f2 ** (q / 2))) ** (1 / q)

def hurst_dfa(r, escalas, q=None):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 4 * escalas.max() or r.std() == 0: return np.nan
    y = np.cumsum(r - r.mean())
    F = np.array([_fluct(y, s, q) for s in escalas])
    ok = np.isfinite(F) & (F > 0)
    if ok.sum() < 4: return np.nan
    return np.polyfit(np.log(escalas[ok]), np.log(F[ok]), 1)[0]

def hurst_rs(r, escalas):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    out = []
    for s in escalas:
        n = len(r) // s
        if n < 4: out.append(np.nan); continue
        seg = r[: n * s].reshape(n, s)
        z = np.cumsum(seg - seg.mean(1, keepdims=True), 1)
        R = z.max(1) - z.min(1); S = seg.std(1)
        ok = S > 0
        out.append((R[ok] / S[ok]).mean() if ok.sum() >= 4 else np.nan)
    out = np.array(out); ok = np.isfinite(out) & (out > 0)
    return np.polyfit(np.log(escalas[ok]), np.log(out[ok]), 1)[0] if ok.sum() >= 4 else np.nan

def fgn(n, H, rng):
    """Ruido gaussiano fraccional (Davies-Harte)."""
    k = np.arange(n + 1)
    g = 0.5 * ((k + 1.0) ** (2 * H) - 2 * k ** (2 * H) + np.abs(k - 1.0) ** (2 * H))
    c = np.concatenate([g, g[-2:0:-1]]); lam = np.fft.fft(c).real
    lam[lam < 0] = 0; m = len(c)
    w = rng.normal(size=m) + 1j * rng.normal(size=m)
    return np.fft.fft(np.sqrt(lam / m) * w).real[:n]

def prueba():
    rng = np.random.default_rng(14)
    for H in [0.3, 0.5, 0.7]:
        a5 = [hurst_dfa(fgn(1900, H, rng), E5) for _ in range(200)]
        ah = [hurst_dfa(fgn(390, H, rng), EH) for _ in range(200)]
        ar = [hurst_rs(fgn(1900, H, rng), E5) for _ in range(200)]
        print(f"H real {H}: DFA 5 ses {np.mean(a5):.3f} (de {np.std(a5):.3f}) | DFA 390 {np.mean(ah):.3f} (de {np.std(ah):.3f}) | R/S {np.mean(ar):.3f}")

def cargar(d, lado, tz):
    fs = [f for f in sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv")) if os.path.getsize(f) > 0]
    df = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit="ms", utc=True)).tz_convert(tz)
    return df[["close"]]

if __name__ == "__main__":
    if sys.argv[1] == "prueba": prueba(); sys.exit()
    sim, d, anio, salida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    tz, a0, fin = MERC[sim]
    b, a = cargar(d, "bid", tz), cargar(d, "ask", tz)
    idx = b.index.intersection(a.index)
    px = ((b.close.loc[idx] + a.close.loc[idx]) / 2)
    lp = np.log(px.values); tmin = px.index.hour * 60 + px.index.minute
    fechas = np.asarray(px.index.year * 10000 + px.index.month * 100 + px.index.day)
    a_fecha = lambda k: date(k // 10000, k // 100 % 100, k % 100)
    # rendimientos dentro de la sesión propia de cada día
    ses = {}
    lim = {}
    for k in pd.unique(fechas):
        f = a_fecha(int(k))
        if f.weekday() >= 5: continue
        lo, hi = np.searchsorted(fechas, k, "left"), np.searchsorted(fechas, k, "right")
        lim[f] = (lo, hi)
        m = np.arange(lo, hi)[(tmin[lo:hi] >= a0) & (tmin[lo:hi] < fin(f))]
        if len(m) >= 60: ses[f] = np.diff(lp[m])
    dias = sorted(ses)
    filas = []
    pos_por_fecha = {f: i for i, f in enumerate(dias)}
    for f in dias:
        if f.year != anio: continue
        i = pos_por_fecha[f]
        fila = dict(fecha=f, sim=sim)
        if i >= 5:
            r5 = np.concatenate([ses[g] for g in dias[i - 5:i]])
            fila.update(h5=hurst_dfa(r5, E5), hrs5=hurst_rs(r5, E5),
                        dh5=hurst_dfa(r5, E5, q=-2) - hurst_dfa(r5, E5, q=2), n5=len(r5))
        # 390 rendimientos hasta la entrada (minuto a0+10 del día f, sin incluirlo)
        lo, hi = lim[f]
        m_dia = np.arange(lo, hi)[tmin[lo:hi] < a0 + 10]
        if len(m_dia):
            j = m_dia[-1] + 1  # posiciones [j-391, j) -> 390 rendimientos
            if j >= 391:
                fila["hhoy"] = hurst_dfa(np.diff(lp[j - 391:j]), EH)
        filas.append(fila)
    pd.DataFrame(filas).to_csv(salida, index=False, float_format="%.5g")
    print(sim, anio, len(filas))
