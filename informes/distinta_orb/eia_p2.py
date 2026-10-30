# P2 de la deriva EIA: meseta de parámetros (ventana de entrada, hora de salida) y stop real recorriendo M1.
# Uso: python3 eia_p2.py [oos]
import pandas as pd, numpy as np, sys
OOS = len(sys.argv) > 1 and sys.argv[1] == "oos"
M = pd.read_pickle("USOIL_M1.pkl")
dd = M.resample("1D").agg({"high": "max", "low": "min", "close": "last"}).dropna()
tr = pd.concat([dd.high - dd.low, (dd.high - dd.close.shift()).abs(), (dd.low - dd.close.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(14).mean().shift(1)                      # ATR diario conocido antes del día
m = M[M.index >= "2023-01-01"] if OOS else M[(M.index >= "2021-01-01") & (M.index < "2023-01-01")]
m = m[m.index.dayofweek == 2]
dias = {k: g for k, g in m.groupby(m.index.normalize())}

def hm(h, mi): return pd.Timedelta(hours=h, minutes=mi)
def op(g, d, w, salida, stop_atr):
    t0 = d + hm(17, 30); te = d + hm(17, 30 + w - 1) if w <= 30 else None
    if t0 not in g.index or te not in g.index: return None
    o0, ent = g.at[t0, "open"], g.at[te, "close"]
    if ent == o0: return None
    s = np.sign(ent - o0)
    tramo = g[(g.index > te) & (g.index <= d + salida)]
    if len(tramo) < 10: return None
    sal = tramo.close.iloc[-1]
    cost = g.at[te, "spread"]
    if stop_atr:
        dist = stop_atr * atr.get(d, np.nan)
        if not dist > 0: return None
        stp = ent - s * dist
        toc = tramo.low <= stp if s > 0 else tramo.high >= stp
        if toc.any():
            b = tramo[toc].iloc[0]
            sal = min(stp, b.open) if s > 0 else max(stp, b.open)   # hueco: se llena a la apertura
        return dict(fecha=d, r_bruto=s * (sal - ent) / dist, coste_r=cost / dist)
    return dict(fecha=d, pb=s * (sal / ent - 1) * 1e4, coste_pb=cost / ent * 1e4)

salidas = {"13:30": hm(20, 29), "14:00": hm(20, 59), "14:30": hm(21, 29), "15:00": hm(21, 59)}
print("Sin stop, bruto en pb (t) por ventana de entrada × hora de salida NY")
for w in [3, 5, 10, 15]:
    fila = []
    for k, sal in salidas.items():
        x = pd.DataFrame([r for d, g in dias.items() if (r := op(g, d, w, sal, None))])
        fila.append(f"{k}: {x.pb.mean():6.1f} ({x.pb.mean() / x.pb.std() * np.sqrt(len(x)):4.2f})")
    print(f"entrada {w:2d} min |", " | ".join(fila))
print("\nBase (5 min, salida 14:30 NY) con stop en múltiplos del ATR diario, R neta")
for sa in [0.25, 0.5, 1.0]:
    x = pd.DataFrame([r for d, g in dias.items() if (r := op(g, d, 5, salidas["14:30"], sa))])
    n = x.r_bruto - x.coste_r
    print(f"stop {sa} ATR: ops {len(x)} bruto {x.r_bruto.mean():.3f} R coste {x.coste_r.mean():.3f} R neto {n.mean():.3f} "
          f"t {n.mean() / n.std() * np.sqrt(len(n)):.2f} | por año", x.assign(n=n).groupby(x.fecha.dt.year).n.mean().round(3).to_dict())
    x.to_csv(f"eia_ops_stop{sa}{'_oos' if OOS else ''}.csv", index=False)
