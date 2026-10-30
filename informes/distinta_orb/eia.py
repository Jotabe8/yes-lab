# B. Deriva tras el inventario de crudo EIA (miércoles 10:30 NY = 17:30 servidor) en USOIL M1 FTMO.
# Uso: python3 eia.py [oos]
import pandas as pd, numpy as np, sys
OOS = len(sys.argv) > 1 and sys.argv[1] == "oos"
rng = np.random.default_rng(1)
m = pd.read_pickle("USOIL_M1.pkl")
m = m[(m.index >= "2023-01-01")] if OOS else m[(m.index >= "2021-01-01") & (m.index < "2023-01-01")]
d = m.index.normalize()

def at(hhmm, col):
    s = m[m.index.strftime("%H:%M") == hhmm][col]
    s.index = s.index.normalize()
    return s

o0 = at("17:30", "open"); c5 = at("17:34", "close"); sp5 = at("17:34", "spread")
salidas = {"B1": at("18:29", "close"), "B2": at("21:29", "close")}
rng_ini = (c5 - o0).abs() / c5 * 1e4                       # tamaño del primer movimiento en pb
df = pd.concat({"o0": o0, "c5": c5, "sp": sp5, "B1": salidas["B1"], "B2": salidas["B2"], "mov": rng_ini}, axis=1).dropna()
df = df[df.c5 != df.o0]
df["dow"] = df.index.dayofweek
df["dir"] = np.sign(df.c5 - df.o0)
for b in ["B1", "B2"]:
    df[b + "_pb"] = df.dir * (df[b] / df.c5 - 1) * 1e4
df["coste_pb"] = df.sp / df.c5 * 1e4
filas = []
for dow, g in df.groupby("dow"):
    for b in ["B1", "B2"]:
        x = g[b + "_pb"]
        filas.append(dict(dia="LMXJV"[dow], regla=b, n=len(x), mov_ini_pb=g.mov.mean(), bruto_pb=x.mean(),
                          t=x.mean() / x.std() * np.sqrt(len(x)), coste_pb=g.coste_pb.mean(),
                          bruto_x_coste=x.mean() / g.coste_pb.mean()))
res = pd.DataFrame(filas)
print(res.round(2).to_string())
w = df[df.dow == 2]
for b in ["B1", "B2"]:
    otros = res[(res.dia != "X") & (res.regla == b)].bruto_pb
    absr = (w[b] / w.c5 - 1).abs() * 1e4
    pl = [(rng.choice([-1, 1], len(w)) * (w[b] / w.c5 - 1) * 1e4).mean() for _ in range(200)]
    print(b, "miércoles", round(w[b + "_pb"].mean(), 2), "| máximo otros días", round(otros.max(), 2),
          "| p95 dirección al azar", round(np.percentile(pl, 95), 2), "| recorrido medio |r|", round(absr.mean(), 1))
    print("   por año:", w.groupby(w.index.year)[b + "_pb"].mean().round(1).to_dict())
res.to_csv("eia_oos.csv" if OOS else "eia_ajuste.csv", index=False)
