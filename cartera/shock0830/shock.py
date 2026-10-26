# Continuación del shock de 08:30 NY (ver PREREGISTRO.md).
import numpy as np, pandas as pd
from embudo import embudo, t_stat

COM = {"XAUUSD": 0.05, "EURUSD": 0.00005}   # ida y vuelta en unidades de precio; índices sin comisión
UMBRAL, SALIDA = 3.0, (10, 0)

def ops_mercado(par):
    v = pd.read_pickle(f"ny_{par}.pkl")
    v = v[~v.index.duplicated()].sort_index()
    filas = []
    dias = {f: d for f, d in v.groupby(v.index.date)}
    rangos = {}
    for f in sorted(dias):
        d = dias[f]
        t0 = pd.Timestamp(f) + pd.Timedelta(hours=8, minutes=30)
        tr = d.loc[t0:t0 + pd.Timedelta(minutes=4)]
        if len(tr) < 5: continue
        rango = tr.high.max() - tr.low.min()
        hist = [rangos[g] for g in sorted(rangos) if g < f][-60:]
        rangos[f] = rango
        if len(hist) < 60 or rango <= UMBRAL * np.median(hist): continue
        t1 = t0 + pd.Timedelta(minutes=5)
        tsal = pd.Timestamp(f) + pd.Timedelta(hours=SALIDA[0], minutes=SALIDA[1])
        if t1 not in d.index or tsal not in d.index: continue
        lado = 1 if tr.close.iloc[-1] > tr.open.iloc[0] else -1
        e, st = d.at[t1, "open"], rango
        tramo = d.loc[t1:tsal - pd.Timedelta(minutes=1)]
        golpe = (tramo.low.min() <= e - st) if lado > 0 else (tramo.high.max() >= e + st)
        rb = -1.0 if golpe else lado * (d.at[tsal, "open"] - e) / st
        coste = (d.at[t1, "spread"] + COM.get(par, 0.0)) / st
        filas.append((pd.Timestamp(f), rb, coste, lado, st / e))
    return pd.DataFrame(filas, columns=["fecha", "r_bruto", "coste_r", "lado", "stop_pct"])

pares = {"XAUUSD": "XAUUSD", "US500": "USA500IDXUSD", "US30": "USA30IDXUSD", "US2000": "USSC2000IDXUSD", "EURUSD": "EURUSD"}
rng = np.random.default_rng(0)
todo = {}
for nombre, par in pares.items():
    o = ops_mercado(par); todo[nombre] = o
    o.to_csv(f"ops_{nombre}.csv", index=False)
    n_a = (o.fecha < "2023").sum()
    print(f"\n=== {nombre}: {len(o)} ops ({len(o)/8.8:.0f}/año), coste {o.coste_r.mean():.3f} R, stop {o.stop_pct.mean()*100:.2f} % del precio")
    print(f"    bruto {o.r_bruto.mean():+.3f} R t {t_stat(o.r_bruto):.2f} | 2018-22 {o[o.fecha<'2023'].r_bruto.mean():+.3f} (n {n_a})"
          f" | 2023-26 {o[o.fecha>='2023'].r_bruto.mean():+.3f} (n {len(o)-n_a})")
    print("    neto por año:", (o.r_bruto - o.coste_r).groupby(o.fecha.dt.year).mean().round(3).to_dict())

junto = pd.concat(todo.values()).sort_values("fecha").reset_index(drop=True)
print(f"\n### CARTERA (5 mercados): {len(junto)} ops, bruto {junto.r_bruto.mean():+.3f} t {t_stat(junto.r_bruto):.2f}")
plac = lambda s: junto.r_bruto.to_numpy() * np.random.default_rng(s).choice([-1, 1], len(junto))
print(embudo(junto, n_pruebas=10, corte_oos="2023-01-01", placebo=plac))
