# ORB en otros horarios: cada mercado en la apertura de cada bolsa, con barras de 30 min.
# Regla fija (la del ORB, en 30 min): dirección del cuerpo de la primera barra (≥ 10 % del rango),
# entrada al cierre de esa barra, stop 0,15 ATR(14) diario, sin objetivo, salida al cierre de la ventana.
# Uso: python3 orb_horas.py [oos]
import pandas as pd, numpy as np, sys
OOS = len(sys.argv) > 1 and sys.argv[1] == "oos"
rng = np.random.default_rng(1)
import os
MERC = os.environ.get("MERC", "US100,US500,US30,US2000,GER40,UK100,FRA40,EU50,JP225,XAUUSD,USOIL").split(",")
# hora de la barra de apertura (servidor) → última barra de la ventana
HORAS = {"Tokio 02:00": ("02:00", "08:30"), "Europa 10:00": ("10:00", "22:30"),
         "Datos EE. UU. 15:30": ("15:30", "22:30"), "NY 16:30": ("16:30", "22:30")}

def ops(k, h0, h1):
    b = pd.read_pickle(f"b30_{k}.pkl")
    b = b[b.index.dayofweek < 5]
    d = b.index.normalize()
    dd = b.groupby(d).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    tr = pd.concat([dd.high - dd.low, (dd.high - dd.close.shift()).abs(), (dd.low - dd.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    hh = b.index.strftime("%H:%M")
    filas = []
    for dia, g in b.groupby(d):
        g = g[(g.index.strftime("%H:%M") >= h0) & (g.index.strftime("%H:%M") <= h1)]
        if len(g) < 3 or g.index[0].strftime("%H:%M") != h0: continue
        a = atr.get(dia, np.nan)
        if not a > 0: continue
        f = g.iloc[0]; cuerpo = f.close - f.open
        if f.high - f.low <= 0 or abs(cuerpo) < 0.1 * (f.high - f.low): continue
        s = np.sign(cuerpo); ent = f.close; dist = 0.15 * a; stp = ent - s * dist
        resto = g.iloc[1:]
        toc = (resto.low <= stp) if s > 0 else (resto.high >= stp)
        if toc.any():
            x = resto[toc].iloc[0]
            sal = min(stp, x.open) if s > 0 else max(stp, x.open)
        else:
            sal = resto.close.iloc[-1]
        # recorrido de la dirección contraria para el placebo (mismo stop y salida)
        stp2 = ent + s * dist
        toc2 = (resto.high >= stp2) if s > 0 else (resto.low <= stp2)
        if toc2.any():
            x = resto[toc2].iloc[0]
            sal2 = max(stp2, x.open) if s > 0 else min(stp2, x.open)
        else:
            sal2 = resto.close.iloc[-1]
        filas.append(dict(fecha=dia, r=s * (sal - ent) / dist, r_contra=-s * (sal2 - ent) / dist,
                          coste=f.spread / dist))
    return pd.DataFrame(filas)

res = []
for k in MERC:
    for nom, (h0, h1) in HORAS.items():
        o = ops(k, h0, h1)
        if o.empty: continue
        o = o[o.fecha >= "2023-01-01"] if OOS else o[(o.fecha >= "2018-01-01") & (o.fecha < "2023-01-01")]
        if len(o) < 100: continue
        neto = o.r - o.coste
        # placebo: dirección al azar con las mismas salidas
        pl = [np.where(rng.random(len(o)) < 0.5, o.r, o.r_contra).mean() for _ in range(200)]
        res.append(dict(mercado=k, hora=nom, ops=len(o), bruto=o.r.mean(), coste=o.coste.mean(), neto=neto.mean(),
                        t=neto.mean() / neto.std() * np.sqrt(len(o)), placebo_p95=np.percentile(pl, 95),
                        anios_pos=(neto.groupby(o.fecha.dt.year).mean() > 0).mean()))
        print(res[-1], flush=True)
df = pd.DataFrame(res)
df.to_csv(("orb_horas_oos" if OOS else "orb_horas_ajuste") + os.environ.get("SUF", "") + ".csv", index=False)
pd.set_option("display.width", 200)
print(df.round(3).to_string())
