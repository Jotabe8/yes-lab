"""Convierte M1 bid/ask de Dukascopy de una acción en una fila por día con el resultado del ORB
de 5 min en las dos direcciones y con los dos stops del preregistro (A: 10 % ATR14, B: otro
extremo del rango). Así el placebo (dirección aleatoria) y las 4 variantes se calculan después
sin volver a bajar datos.

Uso: python procesar.py SIMBOLO dir_csv salida.csv
Convenciones: precios medios (bid+ask)/2 para señal, stop y salida; el coste se apunta aparte:
media horquilla a la entrada + media a la salida + comisión 0,004 % por lado (supuesto FTMO).
El stop se comprueba vela a vela; si la vela abre más allá del stop se llena a la apertura.
En la vela de entrada, si toca el stop también se cuenta como stop (conservador).
"""
import sys, glob
import numpy as np, pandas as pd

COMISION = 0.00004  # por lado, fracción del precio


def cargar(d, lado):
    fs = sorted(glob.glob(f"{d}/*-m1-{lado}-*.csv"))
    df = pd.concat([pd.read_csv(f) for f in fs if __import__("os").path.getsize(f) > 0], ignore_index=True)
    df = df.drop_duplicates("timestamp").sort_values("timestamp")
    df.index = pd.to_datetime(df.timestamp, unit="ms", utc=True).dt.tz_convert("America/New_York")
    return df[["open", "high", "low", "close", "volume"]]


def main(sim, d, salida):
    b, a = cargar(d, "bid"), cargar(d, "ask")
    idx = b.index.intersection(a.index)
    b, a = b.loc[idx], a.loc[idx]
    m = (b[["open", "high", "low", "close"]] + a[["open", "high", "low", "close"]]) / 2
    m["spr"] = (a.close - b.close).clip(lower=0)
    m["vol"] = b.volume + a.volume
    hm = m.index.hour * 60 + m.index.minute
    m = m[(hm >= 570) & (hm < 960)]  # 9:30-16:00 NY
    m["fecha"] = m.index.date
    filas, diarios = [], []
    for f, g in m.groupby("fecha", sort=True):
        t = g.index.hour * 60 + g.index.minute
        diarios.append((f, g.open.iloc[0], g.high.max(), g.low.min(), g.close.iloc[-1]))
        r5 = g[t < 575]
        if len(r5) < 4 or t[0] != 570 or (t >= 955).sum() == 0:
            continue
        O, C, H, L = r5.open.iloc[0], r5.close.iloc[-1], r5.high.max(), r5.low.min()
        fila = dict(fecha=f, sim=sim, precio=O, o5=O, c5=C, h5=H, l5=L, vol5=r5.vol.sum(),
                    dir=int(np.sign(C - O)))
        post = g[(t >= 575) & (t < 955)]
        tp = post.index.hour * 60 + post.index.minute
        sal = g[t >= 955].iloc[0]
        for lado, nivel in (("L", H), ("S", L)):
            ventana = post[tp < 630]
            hit = ventana.high >= nivel if lado == "L" else ventana.low <= nivel
            if not hit.any():
                fila[f"trig_{lado}"] = 0
                continue
            i0 = np.flatnonzero(hit.values)[0]
            vb = ventana.iloc[i0]
            ent = max(nivel, vb.open) if lado == "L" else min(nivel, vb.open)
            fila[f"trig_{lado}"] = 1
            fila[f"ent_{lado}"] = ent
            fila[f"spr_ent_{lado}"] = vb.spr
            resto = post.iloc[post.index.get_loc(ventana.index[i0]):]
            for st in ("A", "B"):
                # A se completa luego con el ATR (aquí solo guardamos el recorrido adverso y el
                # precio de salida vela a vela para distancias de stop dadas): se guarda la
                # excursión adversa máxima previa a cada vela no hace falta; calculamos B aquí
                if st == "B":
                    stop = L if lado == "L" else H
                    dist = abs(ent - stop)
                    if dist <= 0:
                        continue
                    fila[f"r_B_{lado}"], fila[f"spr_sal_B_{lado}"] = recorrer(resto, ent, stop, lado, sal)
                    fila[f"dist_B_{lado}"] = dist
            # para el stop A guardamos la serie de excursión adversa acumulada: se resuelve con ATR
            fila[f"_resto_{lado}"] = (resto, ent)
        fila["_sal"] = sal
        filas.append(fila)
    dd = pd.DataFrame(diarios, columns=["fecha", "o", "h", "l", "c"]).set_index("fecha")
    pc = dd.c.shift(1)
    tr = pd.concat([dd.h - dd.l, (dd.h - pc).abs(), (dd.l - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)  # solo días anteriores
    out = []
    for fila in filas:
        a14 = atr.get(fila["fecha"], np.nan)
        fila["atr14"] = a14
        sal = fila.pop("_sal")
        for lado in ("L", "S"):
            x = fila.pop(f"_resto_{lado}", None)
            if x is None or not np.isfinite(a14):
                continue
            resto, ent = x
            dist = 0.10 * a14
            stop = ent - dist if lado == "L" else ent + dist
            fila[f"r_A_{lado}"], fila[f"spr_sal_A_{lado}"] = recorrer(resto, ent, stop, lado, sal)
            fila[f"dist_A_{lado}"] = dist
        out.append(fila)
    pd.DataFrame(out).to_csv(salida, index=False, float_format="%.6g")
    print(sim, len(out), "días")


def recorrer(resto, ent, stop, lado, sal):
    dist = abs(ent - stop)
    for i in range(len(resto)):
        v = resto.iloc[i]
        if lado == "L" and v.low <= stop:
            px = min(stop, v.open) if i > 0 else stop
            return (px - ent) / dist, v.spr
        if lado == "S" and v.high >= stop:
            px = max(stop, v.open) if i > 0 else stop
            return (ent - px) / dist, v.spr
    px = sal.open
    return ((px - ent) if lado == "L" else (ent - px)) / dist, sal.spr


if __name__ == "__main__":
    main(*sys.argv[1:4])
