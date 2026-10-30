# A. Periodicidad intradía: ir en la dirección de la media de la misma media hora en días anteriores.
# Uso: python3 periodicidad.py [oos]   (sin argumento solo 2018-2022)
import pandas as pd, numpy as np, sys
OOS = len(sys.argv) > 1 and sys.argv[1] == "oos"
rng = np.random.default_rng(1)
# sesión de contado en hora servidor (NY+7): primera y última media hora que se operan
SES = {"US500": ("16:30", "22:30"), "US100": ("16:30", "22:30"), "US30": ("16:30", "22:30"), "US2000": ("16:30", "22:30"),
       "GER40": ("10:00", "18:00"), "UK100": ("10:00", "18:00"), "FRA40": ("10:00", "18:00"), "EU50": ("10:00", "18:00"),
       "JP225": ("02:30", "08:30"), "XAUUSD": ("10:00", "22:30")}

def tabla(k):
    b = pd.read_pickle(f"b30_{k}.pkl")
    b = b.between_time(*SES[k])
    b = b[b.index.dayofweek < 5]
    r = (b.close / b.open - 1) * 1e4                       # pb, de apertura a cierre de la media hora
    c = b.spread / b.close * 1e4                           # coste ida y vuelta = un spread
    R = r.groupby([b.index.normalize(), b.index.strftime("%H:%M")]).first().unstack()
    C = c.groupby([c.index.normalize(), c.index.strftime("%H:%M")]).first().unstack()
    R = R[R.notna().mean(axis=1) > 0.8]                     # días casi completos
    return R, C.reindex(R.index)

def senales(R):
    s1 = R.shift(1).rolling(20, min_periods=15).mean()     # A1: últimos 20 días
    dow = R.index.dayofweek
    s2 = R.copy() * np.nan                                  # A2: mismo día de la semana, 8 semanas
    for d in range(5):
        m = dow == d
        s2[m] = R[m].shift(1).rolling(8, min_periods=6).mean()
    return {"A1": s1, "A2": s2}

def resultado(R, C, S):
    pos = np.sign(S)
    g = (pos * R).stack()
    cost = C.where(pos.notna() & R.notna()).stack()
    return g.mean(), g.std() / np.sqrt(len(g)), cost.mean(), len(g)

filas = []
for k in SES:
    R, C = tabla(k)
    if OOS: m = R.index >= "2023-01-01"
    else:   m = (R.index >= "2018-01-01") & (R.index < "2023-01-01")
    for nom, S in senales(R).items():
        Rm, Cm, Sm = R[m], C[m], S[m]
        g, se, cost, n = resultado(Rm, Cm, Sm)
        # placebo: la señal de otra media hora (permutación de columnas), 200 réplicas
        cols = list(Sm.columns); pl = []
        for _ in range(200):
            p = rng.permutation(cols)
            Sp = Sm[p].copy(); Sp.columns = cols
            pl.append(resultado(Rm, Cm, Sp)[0])
        filas.append(dict(mercado=k, regla=nom, ops=n, bruto_pb=g, t=g / se, coste_pb=cost,
                          bruto_x_coste=g / cost, placebo_p95=np.percentile(pl, 95), neto_pb=g - cost))
        print(filas[-1], flush=True)
df = pd.DataFrame(filas)
df.to_csv("periodicidad_oos.csv" if OOS else "periodicidad_ajuste.csv", index=False)
print(df.round(3).to_string())
for nom in ["A1", "A2"]:
    d = df[df.regla == nom]
    print(nom, "bruto medio", round(d.bruto_pb.mean(), 3), "coste medio", round(d.coste_pb.mean(), 3),
          "mercados +", (d.bruto_pb > 0).sum(), "sobre p95", (d.bruto_pb > d.placebo_p95).sum())
