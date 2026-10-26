# Recalcula cada operación de la noche con el recorrido M1 completo: el stop salta en la primera
# vela que lo toca y se llena al peor de (stop, apertura de esa vela), así que un hueco cuesta más de 1 R.
import sys, numpy as np, pandas as pd
nom = sys.argv[1]
FICH = {"US500": "USA500IDXUSD_M1_DUKA", "US30": "USA30IDXUSD_M1_DUKA", "US2000": "USSC2000IDXUSD_M1_DUKA",
        "FRA40": "FRAIDXEUR_M1_DUKA", "EU50": "EUSIDXEUR_M1_DUKA", "UK100": "GBRIDXGBP_M1_DUKA", "GER40": "GER40_M1_FTMO"}
US = nom.startswith("US")
desf, h_ci, h_sal = (7, 16.0, 9.58) if US else (1, 21.9, 9.1)
o = pd.read_csv("ops_noche_sin_tope.csv", parse_dates=["fecha"]); o = o[o.mercado == nom].reset_index(drop=True)
fechas = set()
for f in o.fecha:
    for k in range(7): fechas.add(str((f + pd.Timedelta(days=k)).date()))
partes = []
for ch in pd.read_csv(f"../../data/{FICH[nom]}.csv", chunksize=1_000_000, engine="c"):
    m = ch.time.str[:10].isin(fechas)
    if m.any():
        w = ch[m.values]
        t = pd.to_datetime(w.time, format="%Y-%m-%d %H:%M:%S") - pd.Timedelta(hours=desf)
        w = w[["open", "high", "low", "close", "spread"]].copy(); w.index = t.values; partes.append(w)
v = pd.concat(partes).sort_index(); v = v[~v.index.duplicated()]
filas = []
for _, op in o.iterrows():
    t_ci = op.fecha + pd.Timedelta(hours=h_ci)
    i0 = v.index.searchsorted(t_ci)
    if i0 >= len(v) or abs((v.index[min(i0, len(v)-1)] - t_ci).total_seconds()) > 900: i0 = max(i0 - 1, 0)
    e = v.close.iloc[i0]; st = e * 0.01; stop = e - st
    # salida: primera vela a partir de h_sal en un día posterior
    tras = v.iloc[i0 + 1:v.index.searchsorted(t_ci + pd.Timedelta(days=6))]
    dias_post = sorted({d for d in tras.index.date if d > op.fecha.date()})
    t_sal = None
    for d in dias_post:
        cand = tras[(tras.index >= pd.Timestamp(d) + pd.Timedelta(hours=h_sal))]
        cand = cand[cand.index.date == d]
        if len(cand): t_sal = cand.index[0]; break
    if t_sal is None: continue
    tramo = tras[tras.index < t_sal]
    toca = tramo[tramo.low <= stop]
    if len(toca):
        b = toca.iloc[0]; fill = min(stop, b.open); rb = (fill - e) / st; motivo = "hueco" if b.open < stop else "stop"
    else:
        rb = (v.at[t_sal, "open"] - e) / st; motivo = "hora"
    filas.append((op.fecha, nom, rb, op.coste_r, op.fecha.weekday(), motivo))
r = pd.DataFrame(filas, columns=["fecha", "mercado", "r_bruto", "coste_r", "dia_sem", "salida"])
r.to_csv(f"real_{nom}.csv", index=False)
print(nom, len(r), "bruto", round(r.r_bruto.mean(), 3), "| salidas", r.salida.value_counts().to_dict(), "| peor", round(r.r_bruto.min(), 2),
      "| sin viernes", round(r[r.dia_sem != 4].r_bruto.mean(), 3))
