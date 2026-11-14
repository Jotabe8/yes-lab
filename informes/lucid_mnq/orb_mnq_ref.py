# Réplica Python de ORB_MNQ_Lucid.cs (NinjaTrader 8), misma lógica y mismo reloj que el NinjaScript (14-11-2026).
# Sirve para validar el port: se compara día a día con la serie v018 (serie_v018_be.csv: R = reto con trailing 3R/1R,
# Rbe = fondeada con stop a entrada a +2R) y da las distancias de stop en puntos para dimensionar en micros MNQ.
#
# Reglas (idénticas al .cs):
#  - Velas M1 con sello de CIERRE (como NinjaTrader). Reloj de Nueva York (ET).
#  - Rango = velas que cierran en (9:30, 9:40]. Hacen falta >= 8 velas y la primera debe cerrar <= 9:33.
#  - Cuerpo = cierre de la vela de 9:40 - apertura de la primera. |cuerpo| < 10 % del rango -> no opera.
#  - Entrada a mercado al cierre de la vela de 9:40 -> se llena en la apertura de la vela siguiente (<= 9:45).
#  - Stop = 15 % del ATR(14) diario de AYER (media simple del TR, como iATR de MT5), redondeado a tick (0,25).
#    Velas diarias de 17:00 a 17:00 ET (sesión ETH de CME = día del servidor FTMO).
#  - Filtro de volatilidad: no opera si ATR/cierre de ayer supera el percentil 90 de los 252 días anteriores
#    (si hay < 120 días de historia, no filtra).
#  - Reto (fase 0): trailing al llegar a +3R con el stop a 1R del máximo favorable (paso mínimo 0,1R).
#    Fondeada (fase 2): stop a entrada al llegar a +2R. Se evalúa al cierre de cada vela M1 (como el .cs).
#  - Stop tocado dentro de la vela: se llena al stop, o a la apertura si la vela abre ya pasado el stop.
#  - Salida a las 15:30 ET (cierre de la vela de 15:30); en días de FOMC a las 14:00 ET.
#  - Días bloqueados: festivos y cierres anticipados de la lista del v018.
# Uso: python3 orb_mnq_ref.py M1.csv [M1_extra.csv ...] -o salida.csv
#   M1 en hora del servidor FTMO (NY+7) con columnas time,open,high,low,close[,spread]; spread en puntos*100 (FTMO).
import sys, numpy as np, pandas as pd

HOL = """2024.01.01 2024.01.15 2024.02.19 2024.03.29 2024.05.27 2024.06.19 2024.07.03 2024.07.04 2024.09.02 2024.11.28
2024.11.29 2024.12.24 2024.12.25 2025.01.01 2025.01.09 2025.01.20 2025.02.17 2025.04.18 2025.05.26 2025.06.19 2025.07.03
2025.07.04 2025.09.01 2025.11.27 2025.11.28 2025.12.24 2025.12.25 2026.01.01 2026.01.19 2026.02.16 2026.04.03 2026.05.25
2026.06.19 2026.07.03 2026.09.07 2026.11.26 2026.11.27 2026.12.24 2026.12.25""".split()
FOMC = """2024.01.31 2024.03.20 2024.05.01 2024.06.12 2024.07.31 2024.09.18 2024.11.07 2024.12.18 2025.01.29 2025.03.19
2025.05.07 2025.06.18 2025.07.30 2025.09.17 2025.10.29 2025.12.10 2026.01.28 2026.03.18 2026.04.29 2026.06.17 2026.07.29
2026.09.16 2026.10.28 2026.12.09""".split()
HOL = {pd.Timestamp(x.replace(".", "-")).date() for x in HOL}
FOMC = {pd.Timestamp(x.replace(".", "-")).date() for x in FOMC}
TICK = 0.25

def carga(fs):
    df = pd.concat([pd.read_csv(f, parse_dates=["time"]) for f in fs]).drop_duplicates("time").sort_values("time")
    df["sp"] = df.spread * 0.01 if "spread" in df else 0.0
    # servidor = NY+7; sello de cierre (+1 min) como NinjaTrader
    df["et"] = df.time - pd.Timedelta(hours=7) + pd.Timedelta(minutes=1)
    df["dsrv"] = df.time.dt.normalize()                     # día del servidor = sesión 17:00-17:00 ET
    return df.reset_index(drop=True)

def diarios(df):
    g = df.groupby("dsrv").agg(h=("high", "max"), l=("low", "min"), c=("close", "last"), n=("open", "size"))
    g = g[g.n > 300]
    pc = g.c.shift(1)
    tr = np.maximum(g.h - g.l, np.maximum((g.h - pc).abs(), (g.l - pc).abs()))
    g["atr"] = tr.rolling(14).mean()                         # ATR del día (MT5 iATR = media simple del TR)
    g["atrp"] = g.atr / g.c
    # percentil de ayer frente a los 252 anteriores (cuenta estricta, como VolTooHigh)
    a = g.atrp.values; pct = np.full(len(a), np.nan)
    for i in range(len(a)):
        if not np.isfinite(a[i]): continue
        prev = a[max(0, i - 252):i]; prev = prev[np.isfinite(prev)]
        if len(prev) >= 120: pct[i] = 100.0 * (prev < a[i]).sum() / len(prev)
    g["pct"] = pct
    g["atr_ayer"] = g.atr.shift(1); g["pct_ayer"] = g.pct.shift(1)
    return g

def dia(sub, R, fase, act=3.0, dist=1.0, step=0.1, be=2.0, precio="cfd"):
    """sub: velas del día en ET (sello de cierre). Devuelve dict o None. precio: 'cfd' (bid+spread como la serie v018)
    o 'fut' (un solo precio, sin horquilla: el coste se resta luego en $ por contrato)."""
    t = sub.et.dt.hour.values * 60 + sub.et.dt.minute.values
    o, h, l, c = sub.open.values, sub.high.values, sub.low.values, sub.close.values
    sp = sub.sp.values if precio == "cfd" else np.zeros(len(sub))
    rg = np.where((t > 570) & (t <= 580))[0]
    if len(rg) < 8 or t[rg[0]] > 573: return None
    hi, lo = h[rg].max(), l[rg].min(); r = hi - lo
    if r <= 0: return None
    body = c[rg[-1]] - o[rg[0]]
    if abs(body) < 0.10 * r: return None
    if t[rg[-1]] != 580: return None                         # el .cs evalúa al cierre de la vela de 9:40
    dr = 1 if body > 0 else -1
    k = rg[-1] + 1
    if k >= len(t) or t[k] > 585: return None
    fin = 14 * 60 if sub.et.iloc[0].date() in FOMC else 15 * 60 + 30
    ent = o[k] + sp[k] if dr == 1 else o[k]
    stop = ent - dr * R; mfe = 0.0; px = None; motivo = "cierre"
    for j in range(k, len(t)):
        # 1) stop tocado en esta vela (con el stop vigente desde el cierre de la anterior)
        if dr == 1:
            adv = l[j]
            if adv <= stop: px = stop if j == k else min(o[j], stop); motivo = "stop"; break
        else:
            adv = h[j] + sp[j]
            if adv >= stop: px = stop if j == k else max(o[j] + sp[j], stop); motivo = "stop"; break
        # 2) cierre de la vela: actualizar máximo favorable y mover el stop
        fav = (h[j] - ent) if dr == 1 else (ent - (l[j] + sp[j]))
        mfe = max(mfe, fav)
        if fase == 0 and act > 0 and mfe >= act * R:
            ns = ent + dr * (mfe - dist * R)
            if dr * (ns - stop) >= step * R: stop = ns
        if fase == 2 and be > 0 and mfe >= be * R and dr * (ent - stop) > 0:
            stop = ent
        # 3) hora de salida
        if t[j] >= fin:
            px = c[j] if dr == 1 else c[j] + sp[j]; break
    if px is None: return None
    return dict(lado=dr, ent=ent, salida=px, R=dr * (px - ent) / R, motivo=motivo)

def main(fs, out):
    df = carga(fs); g = diarios(df)
    s = df[(df.et.dt.hour * 60 + df.et.dt.minute > 570) & (df.et.dt.hour * 60 + df.et.dt.minute <= 960)]
    filas = []
    for d, sub in s.groupby(s.et.dt.date):
        dsrv = pd.Timestamp(d)
        if dsrv not in g.index or not np.isfinite(g.at[dsrv, "atr_ayer"]): continue
        motivo = None
        if d in HOL: motivo = "festivo"
        elif np.isfinite(g.at[dsrv, "pct_ayer"]) and g.at[dsrv, "pct_ayer"] > 90: motivo = "volatilidad"
        atr = g.at[dsrv, "atr_ayer"]; Rp = max(TICK, round(0.15 * atr / TICK) * TICK)
        fila = dict(d=dsrv, atr=atr, stop_pts=Rp, pct=g.at[dsrv, "pct_ayer"], bloqueo=motivo)
        if motivo is None:
            for nm, fase, precio in (("R_reto", 0, "cfd"), ("R_fond", 2, "cfd"), ("Rf_reto", 0, "fut"), ("Rf_fond", 2, "fut")):
                x = dia(sub, Rp, fase, precio=precio)
                fila[nm] = np.nan if x is None else x["R"]
                if x is not None and nm == "R_reto": fila["lado"] = x["lado"]; fila["motivo"] = x["motivo"]
        filas.append(fila)
    T = pd.DataFrame(filas); T.to_csv(out, index=False, float_format="%.5g"); print(out, len(T), "días,", T.R_reto.notna().sum(), "operaciones")

if __name__ == "__main__":
    a = sys.argv[1:]; i = a.index("-o"); main(a[:i], a[i + 1])
