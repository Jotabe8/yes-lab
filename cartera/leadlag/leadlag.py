# Asia marca el día en Europa (ver PREREGISTRO.md).
import numpy as np, pandas as pd
from embudo import embudo, t_stat

UMBRAL = 0.003   # señal mínima: 0,3 %
def serie(par): 
    v = pd.read_pickle(f"cet_{par}.pkl"); return v[~v.index.duplicated()].sort_index()

jp, hk = serie("JPNIDXJPY"), serie("HKGIDXHKD")

def señal_asia():
    s = {}
    for v, ini in ((jp, "00:00"), (hk, "03:30")):
        for f, d in v.groupby(v.index.date):
            d = d.between_time(ini, "07:00")
            if len(d) > 30:
                s.setdefault(f, []).append(d.close.iloc[-1] / d.open.iloc[0] - 1)
    return {f: float(np.mean(x)) for f, x in s.items() if len(x) == 2}

SEÑ = señal_asia()
print("días con señal de Asia:", len(SEÑ))

def ops(par):
    v = serie(par); filas = []
    for f, d in v.groupby(v.index.date):
        s = SEÑ.get(f)
        if s is None or abs(s) < UMBRAL: continue
        t0 = pd.Timestamp(f) + pd.Timedelta(hours=9)
        tsal = pd.Timestamp(f) + pd.Timedelta(hours=12)
        pre = d.loc[pd.Timestamp(f):t0 - pd.Timedelta(minutes=1)]
        if t0 not in d.index or tsal not in d.index or len(pre) < 60: continue
        st = pre.high.max() - pre.low.min()
        if st <= 0: continue
        lado = 1 if s > 0 else -1
        e = d.at[t0, "open"]
        tramo = d.loc[t0:tsal - pd.Timedelta(minutes=1)]
        golpe = (tramo.low.min() <= e - st) if lado > 0 else (tramo.high.max() >= e + st)
        rb = -1.0 if golpe else lado * (d.at[tsal, "open"] - e) / st
        filas.append((pd.Timestamp(f), rb, d.at[t0, "spread"] / st, lado, st / e))
    return pd.DataFrame(filas, columns=["fecha", "r_bruto", "coste_r", "lado", "stop_pct"])

todo = {}
for nombre, par in {"FRA40": "FRAIDXEUR", "EU50": "EUSIDXEUR", "UK100": "GBRIDXGBP"}.items():
    o = ops(par); todo[nombre] = o; o.to_csv(f"ops_{nombre}.csv", index=False)
    a = o.fecha < "2023"
    print(f"\n=== {nombre}: {len(o)} ops ({len(o)/8.8:.0f}/año), coste {o.coste_r.mean():.3f} R, stop {o.stop_pct.mean()*100:.2f} %")
    print(f"    bruto {o.r_bruto.mean():+.3f} t {t_stat(o.r_bruto):.2f} | 2018-22 {o[a].r_bruto.mean():+.3f} (n {a.sum()}) | 2023-26 {o[~a].r_bruto.mean():+.3f} (n {(~a).sum()})")
    print("    neto por año:", (o.r_bruto - o.coste_r).groupby(o.fecha.dt.year).mean().round(3).to_dict())

junto = pd.concat(todo.values()).sort_values("fecha").reset_index(drop=True)
print(f"\n### CARTERA: {len(junto)} ops, bruto {junto.r_bruto.mean():+.3f} t {t_stat(junto.r_bruto):.2f}")
plac = lambda s: junto.r_bruto.to_numpy() * np.random.default_rng(s).choice([-1, 1], len(junto))
print(embudo(junto, n_pruebas=8, corte_oos="2023-01-01", placebo=plac))
junto.to_csv("ops_cartera.csv", index=False)
