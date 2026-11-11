# Calibración de SPA/StepM y PBO con un caso conocido: el ORB en 11 mercados × 4 aperturas
# (44 variantes, barras 30 min, 2018-2022; PR #14). Ya se sabe que solo las aperturas propias
# US100 NY, GER40 Europa y US500 NY superan al placebo. Se espera:
#   - real: SPA p ≤ 0,05 y StepM con alguna de esas tres; PBO bajo.
#   - placebo (dirección al azar, mismas salidas): SPA p > 0,05 y PBO ≈ 0,5.
# Uso en el PC (Python con arch): python calibracion_robustez.py <carpeta con b30_*.pkl>
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from metodo.robustez import matriz_diaria, spa, pbo

CARPETA = sys.argv[1] if len(sys.argv) > 1 else "."
MERC = "US100,US500,US30,US2000,GER40,UK100,FRA40,EU50,JP225,XAUUSD,USOIL".split(",")
HORAS = {"Tokio": ("02:00", "08:30"), "Europa": ("10:00", "22:30"),
         "Datos": ("15:30", "22:30"), "NY": ("16:30", "22:30")}


def ops(k, h0, h1):  # misma regla que distinta-orb/orb_horas.py
    b = pd.read_pickle(os.path.join(CARPETA, f"b30_{k}.pkl"))
    b = b[b.index.dayofweek < 5]
    d = b.index.normalize()
    dd = b.groupby(d).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    tr = pd.concat([dd.high - dd.low, (dd.high - dd.close.shift()).abs(),
                    (dd.low - dd.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    filas = []
    for dia, g in b.groupby(d):
        g = g[(g.index.strftime("%H:%M") >= h0) & (g.index.strftime("%H:%M") <= h1)]
        if len(g) < 3 or g.index[0].strftime("%H:%M") != h0: continue
        a = atr.get(dia, np.nan)
        if not a > 0: continue
        f = g.iloc[0]; cuerpo = f.close - f.open
        if f.high - f.low <= 0 or abs(cuerpo) < 0.1 * (f.high - f.low): continue
        s = np.sign(cuerpo); ent = f.close; dist = 0.15 * a; resto = g.iloc[1:]
        def salida(sg):
            stp = ent - sg * dist
            toc = (resto.low <= stp) if sg > 0 else (resto.high >= stp)
            if toc.any():
                x = resto[toc].iloc[0]
                return min(stp, x.open) if sg > 0 else max(stp, x.open)
            return resto.close.iloc[-1]
        filas.append(dict(fecha=dia, r=s * (salida(s) - ent) / dist,
                          r_contra=-s * (salida(-s) - ent) / dist, coste=f.spread / dist))
    o = pd.DataFrame(filas)
    return o[(o.fecha >= "2018-01-01") & (o.fecha < "2023-01-01")]


rng = np.random.default_rng(7)
real, placebo = {}, {}
for k in MERC:
    if not os.path.exists(os.path.join(CARPETA, f"b30_{k}.pkl")): continue
    for nom, (h0, h1) in HORAS.items():
        o = ops(k, h0, h1)
        if len(o) < 100: continue
        real[f"{k} {nom}"] = pd.DataFrame({"fecha": o.fecha, "r": o.r - o.coste})
        azar = np.where(rng.random(len(o)) < 0.5, o.r, o.r_contra)
        placebo[f"{k} {nom}"] = pd.DataFrame({"fecha": o.fecha, "r": azar - o.coste})
        print(f"{k:7} {nom:7} {len(o):5} ops neto {(o.r - o.coste).mean():+.3f}", flush=True)

for nombre, dic in (("REAL", real), ("PLACEBO", placebo)):
    m = matriz_diaria(dic)
    sp, pb = spa(m), pbo(m)
    print(f"\n== {nombre}: {m.shape[1]} variantes, {m.shape[0]} días")
    print(f"SPA p {sp['p_spa']:.3f} (cotas {sp['p_bajo']:.3f}-{sp['p_alto']:.3f}), bloque {sp['bloque']:.1f}")
    print(f"mejor {sp['mejor']} {sp['media_mejor']:+.4f} R/día; StepM: {sp['superiores'] or 'ninguna'}")
    print(f"PBO {pb['pbo']:.1%}; Sharpe/día elegida {pb['metrica_in_mejor']:.3f} dentro -> "
          f"{pb['metrica_oos_mejor']:.3f} fuera; P(fuera < 0) {pb['p_oos_negativa']:.1%}")
