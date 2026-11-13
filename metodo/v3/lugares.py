"""Neto de cada ventaja por lugar con costes publicados (13-11-2026). Simulaciones en precio medio ya hechas."""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/metodo/v3/"
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x))
def carga(pat):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(B + pat))); d["fecha"] = pd.to_datetime(d.fecha)
    d = d.set_index("fecha").sort_index(); return d[d.index.dayofweek < 5]
btc = carga("orb_cripto_medio/medio_BTCUSD_*.csv").dropna(subset=["r10"]); btc = btc[btc.index >= "2021-03-01"]
eth = carga("orb_cripto_medio/medio_ETHUSD_*.csv").dropna(subset=["r10"]); eth = eth[eth.index >= "2021-03-01"]
jp = carga("orb_asia/asia_JP225_*.csv").dropna(subset=["r"])
casos = []
def caso(mercado, lugar, r, coste_R, nota):
    n = r - coste_R; m = n.index >= "2024-01-01"
    casos.append(dict(mercado=mercado, lugar=lugar, coste_R=round(coste_R.mean(), 3), neto=round(n.mean(), 3), t=round(t(n), 2),
                      neto_2024_26=round(n[m].mean(), 3), t_2024_26=round(t(n[m]), 2), nota=nota))
for nom, d in (("BTC", btc), ("ETH", eth)):
    dist = 0.15 * d.atr; k = d.px / dist
    caso(nom, "FTMO CFD (0,065 % + horquilla medida)", d.r10, (0.00065 + (0.000012 if nom == "BTC" else 0.00025)) * k, "medido 13-11")
    caso(nom, "FundingPips CFD (0,04 % ida y vuelta + horquilla ~0,03 %)", d.r10, 0.0007 * k, "comisión publicada; horquilla BTC 15-40 $ según agregador")
    if nom == "BTC":
        caso(nom, "Topstep MBT (2,82 $ i/v + 1 tick 0,5 $)", d.r10, 3.32 / (0.1 * dist), "risk/contrato ~40 $")
        caso(nom, "Topstep BTC estándar 5 BTC (aprox. 2×8,77 + 25 $)", d.r10, 42.5 / (5 * dist), "risk/contrato ~2.000 $: no cabe en 50-150K")
    else:
        caso(nom, "Topstep MET (0,72 $ i/v + 1 tick 0,05 $)", d.r10, 0.77 / (0.1 * dist), "risk/contrato ~1,7 $")
k = jp.px / jp.dist
caso("JP225", "FTMO CFD (horquilla 0,0157 % medida)", jp.r, 0.000157 * k, "medido 13-11")
caso("JP225", "Topstep NKD (5,32 $ + 1 tick 25 $)", jp.r, 30.32 / (5 * jp.dist), "risk/contrato = 5 $ × stop ≈ 550-600 $")
caso("JP225", "Topstep NKD con 2 ticks", jp.r, 55.32 / (5 * jp.dist), "apertura de Tokio en Globex: horquilla puede ser 2 ticks")
r = pd.DataFrame(casos); r.to_csv(B + "lugares.csv", index=False, sep=";")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); print(r.to_string(index=False))
print("riesgo NKD por contrato $ (2024-26):", round((5 * jp.dist)["2024":].mean()), "| MBT:", round((0.1 * 0.15 * btc.atr)["2024":].mean(), 1))
