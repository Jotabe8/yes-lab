# Efecto Gotobi (ver PREREGISTRO.md). Calcula la R de la ventana 08:00-09:55 JST en TODOS los días
# hábiles y luego separa gotobi / no gotobi (placebo).
import numpy as np, pandas as pd
from embudo import embudo, t_stat
E, S = (8, 0), (9, 55)
COM = 0.00005  # 5 $/lote ida y vuelta, como fracción del precio

def cargar(p):
    return pd.read_pickle(f"ventana_{p}.pkl"), pd.read_pickle(f"rango_{p}.pkl")

def sintetico(a, b):  # cruce = a * b (EURUSD * USDJPY)
    (va, ra), (vb, rb) = a, b
    j = va.join(vb, lsuffix="_a", rsuffix="_b", how="inner")
    v = pd.DataFrame({k: j[f"{k}_a"] * j[f"{k}_b"] for k in ["open", "high", "low", "close"]})
    v["spread"] = v.close * (j.spread_a / j.close_a + j.spread_b / j.close_b)
    r = pd.DataFrame({"h": ra.h * rb.h, "l": ra.l * rb.l}).dropna()  # aproximación (solo para el stop)
    return v, r

def gotobi(fechas):
    fechas = set(fechas); out = set()
    meses = sorted({(f.year, f.month) for f in fechas})
    for y, m in meses:
        ult = (pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)).day
        for d in [5, 10, 15, 20, 25, ult]:
            f = pd.Timestamp(y, m, min(d, ult))
            while f.weekday() >= 5 or (f.month == 1 and f.day <= 3):
                f -= pd.Timedelta(days=1)
            out.add(f.date())
    return out

def operaciones(v, r, lado):
    rng = (r.h - r.l)
    stop_d = (0.25 * rng.rolling(14).mean().shift(1)).to_dict()
    filas = []
    for f, dia in v.groupby(v.index.date):
        if pd.Timestamp(f).weekday() >= 5: continue
        t0 = pd.Timestamp(f) + pd.Timedelta(hours=E[0], minutes=E[1])
        t1 = pd.Timestamp(f) + pd.Timedelta(hours=S[0], minutes=S[1])
        if t0 not in dia.index or t1 not in dia.index or not stop_d.get(f) or np.isnan(stop_d[f]): continue
        st = stop_d[f]; e = dia.at[t0, "open"]; x = dia.at[t1, "open"]
        tramo = dia.loc[t0:t1 - pd.Timedelta(minutes=1)]
        if lado > 0:
            golpe = tramo.low.min() <= e - st; spr = dia.at[t0, "spread"]
        else:
            golpe = (tramo.high + tramo.spread).max() >= e + dia.at[t0, "spread"] * 0 + st; spr = dia.at[t1, "spread"]
        rb = -1.0 if golpe else lado * (x - e) / st
        filas.append((pd.Timestamp(f), rb, (spr + COM * e) / st))
    return pd.DataFrame(filas, columns=["fecha", "r_bruto", "coste_r"])

uj, eu, gu = cargar("USDJPY"), cargar("EURUSD"), cargar("GBPUSD")
mercados = {"USDJPY": (uj, 1), "EURJPY": (sintetico(eu, uj), 1), "GBPJPY": (sintetico(gu, uj), 1), "EURUSD (control, corto)": (eu, -1)}
rng = np.random.default_rng(1)
for nombre, ((v, r), lado) in mercados.items():
    todas = operaciones(v, r, lado)
    g = gotobi(todas.fecha.dt.date)
    es = todas.fecha.dt.date.isin(g)
    ops, resto = todas[es].reset_index(drop=True), todas[~es].reset_index(drop=True)
    print(f"\n=== {nombre}: {len(ops)} gotobi, {len(resto)} resto | bruto gotobi {ops.r_bruto.mean():+.3f} R (t {t_stat(ops.r_bruto):.2f})"
          f" | resto {resto.r_bruto.mean():+.3f} R (t {t_stat(resto.r_bruto):.2f}) | coste {ops.coste_r.mean():.3f} R | stop medio pips? {''}")
    for per, m in [("2018-22", ops.fecha < "2023"), ("2023-26", ops.fecha >= "2023")]:
        print(f"   {per}: bruto {ops[m].r_bruto.mean():+.3f} t {t_stat(ops[m].r_bruto):.2f} n {m.sum()}")
    print("   por año (neto):", (ops.r_bruto - ops.coste_r).groupby(ops.fecha.dt.year).mean().round(3).to_dict())
    ops.to_csv(f"ops_{nombre.split()[0]}.csv", index=False)
    if nombre == "USDJPY" or "--todo" in __import__("sys").argv:
        plac = lambda s: resto.r_bruto.sample(len(ops), random_state=s).to_numpy()
        print(embudo(ops, n_pruebas=4, corte_oos="2023-01-01", placebo=plac))
