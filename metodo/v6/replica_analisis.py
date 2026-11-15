"""Análisis de la réplica preregistrada (PREREGISTRO_ORB_CRIPTO_REPLICA.md)."""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v6/replica/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))
MON = ["SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT"]
COSTE = 0.0003
todo = {}
for f in sorted(glob.glob(B + "replica_*.csv")):
    d = pd.read_csv(f, parse_dates=["fecha"]).set_index("fecha"); d = d[d.index >= "2021-03-01"]
    s = d.sim.iloc[0]; k = 1 / d.stop_pct_ny
    d["neto"] = d.r_ny - COSTE * k; d["neto2"] = d.r_ny - 2 * COSTE * k
    d["exc"] = (d.r_ny - d.c_ny) / 2; d["ambos"] = (d.r_ny + d.c_ny) / 2; d["ambos01"] = (d.r_h01 + d.c_h01) / 2
    todo[s] = d
    a = d.index >= "2024-01-01"
    print(f"{s:9s} n {d.r_ny.notna().sum():4d} stop {d.stop_pct_ny.mean()*100:.2f} % | bruto {d.r_ny.mean():+.3f} t {t(d.r_ny):5.2f} | neto {d.neto.mean():+.3f} t {t(d.neto):5.2f} "
          f"| 24-26 {d.neto[a].mean():+.3f} | x2 {d.neto2.mean():+.3f} | contrario {d.c_ny.mean():+.3f} | exc {d.exc.mean():+.3f} t {t(d.exc):5.2f} "
          f"| ambos 9:30 {d.ambos.mean():+.3f} vs 01:00 {d.ambos01.mean():+.3f}")
def cart(col):
    return pd.concat([todo[s][col].rename(s) for s in MON if s in todo], axis=1, sort=True).mean(axis=1).dropna()
neto, n2, exc = cart("neto"), cart("neto2"), cart("exc")
h2 = (cart("ambos") - cart("ambos01").reindex(cart("ambos").index)).dropna()
mitad = neto.index[len(neto) // 2]
print("\nCARTERA 8 monedas (coste 0,03 %): días", len(neto))
print(f" 1 neto R/día {neto.mean():+.3f} t {t(neto):.2f}")
print(f" 2 2024-26 {neto['2024':].mean():+.3f} t {t(neto['2024':]):.2f} | 1ª mitad {neto[:mitad].mean():+.3f} 2ª {neto[mitad:].mean():+.3f}")
print(f" 3 costes x2 {n2.mean():+.3f} t {t(n2):.2f}")
print(f" 4 H1 exceso sobre contrario {exc.mean():+.3f} t {t(exc):.2f} | H2 ambos 9:30 - 01:00 {h2.mean():+.3f} t {t(h2):.2f}")
print(f" 5 monedas con neto > 0: {sum(todo[s].neto.mean() > 0 for s in MON if s in todo)} de {sum(s in todo for s in MON)}")
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
j = pd.concat([neto.rename("c"), orb.rename("o")], axis=1, sort=True).dropna()
print(f" 6 corr diaria con v018 {j.c.corr(j.o):.3f} ({len(j)} días comunes)")
print("\nPor año (cartera neta):"); print(neto.groupby(neto.index.year).agg(["mean", "count", "sum"]).round(3).T)
for s in ("ETHUSDT", "BTCUSDT"):
    if s in todo:
        d = todo[s]
        for c in (0.0002, 0.0003, 0.0004):
            n = d.r_ny - c / d.stop_pct_ny
            print(f"{s} coste {c*100:.2f} %: neto {n.mean():+.3f} t {t(n):.2f} | 2024-26 {n['2024':].mean():+.3f} t {t(n['2024':]):.2f}")
        j = pd.concat([(d.r_ny - 0.0003 / d.stop_pct_ny).rename("c"), orb.rename("o")], axis=1, sort=True).dropna()
        print(f"   corr {s} con v018 {j.c.corr(j.o):.3f}")
