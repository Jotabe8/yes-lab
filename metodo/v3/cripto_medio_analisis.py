"""Análisis del candidato 1 (ORB cripto en futuros CME) con la simulación en precio medio.
Preregistro v3 (escrito antes de ver estos datos, 13-11-2026):
  principal: rango 10 min, cartera BTC + ETH en contratos estándar de CME (los micros cuestan 0,2-0,6 R).
  periodo: 2021-03 → 2026-11 (existen los futuros de ETH y la horquilla de Dukascopy es usable); 2018-20 informativo.
  pasa si: neto t >= 2,4 en todo el periodo, segunda mitad > 0, costes x2 > 0, exceso sobre el lado contrario > 0.
"""
import glob, numpy as np, pandas as pd
B = "/home/user/yes-lab/"
C = {"MBT": ("BTCUSD", 0.1, 1.15, 0.20, 0.50), "BTC": ("BTCUSD", 5.0, 8.25, 0.50, 25.0),
     "MET": ("ETHUSD", 0.1, 0.10, 0.20, 0.05), "ETH": ("ETHUSD", 50.0, 6.05, 0.50, 12.5)}
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
S = {}; filas = []
for act in ("BTCUSD", "ETHUSD"):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(B + f"metodo/v3/orb_cripto_medio/medio_{act}_*.csv")))
    d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index(); d = d[d.index.dayofweek < 5]
    dist = 0.15 * d.atr
    for L in (10, 15, 30, 60):
        r, c = d[f"r{L}"], d[f"c{L}"]
        x = {"bruto medio": r, "lado contrario (placebo)": c, "exceso sobre placebo": (r - c) / 2}
        for sym, (a, tam, tasa, com, tick) in C.items():
            if a != act: continue
            k = (2 * (tasa + com + 0.02) + tick) / tam / dist
            x[f"neto {sym}"] = r - k; x[f"neto {sym} x2"] = r - 2 * k
            if L == 10: print(act, sym, "coste medio 2021-26 en R:", round(k["2021":].mean(), 3))
        x["CFD FTMO (0,065 % + horquilla Dukascopy)"] = r - 0.00065 * d.px / dist - d[f"spr{L}"]
        for nom, s in x.items():
            S[(act, L, nom)] = s.dropna()
            for per, m in (("2018-20", s.index < "2021-03-01"), ("2021-23", (s.index >= "2021-03-01") & (s.index < "2024-01-01")),
                           ("2024-26", s.index >= "2024-01-01"), ("2021-26", s.index >= "2021-03-01")):
                y = s[m].dropna(); filas.append(dict(activo=act, rango=L, serie=nom, periodo=per, ops=len(y), R=y.mean(), t=t(y)))
res = pd.DataFrame(filas); res.to_csv(B + "metodo/v3/cripto_medio_resumen.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400)
print(res[res.rango == 10].pivot_table(index=["activo", "serie"], columns="periodo", values=["R", "t"], sort=False).round(3).to_string())
print("\nInformativo rangos 15/30/60 (2021-26):")
q = res[(res.rango != 10) & (res.periodo == "2021-26") & res.serie.isin(["bruto medio", "exceso sobre placebo", "neto BTC", "neto ETH"])]
print(q.pivot_table(index=["activo", "rango"], columns="serie", values="R").round(3).to_string())
print("\nPor año, rango 10, neto contrato estándar:")
for act, sym in (("BTCUSD", "BTC"), ("ETHUSD", "ETH")):
    s = S[(act, 10, f"neto {sym}")]; print(act, s.groupby(s.index.year).agg(["count", "mean"]).round(3).T.to_string())
# cartera principal
bt, et = S[("BTCUSD", 10, "neto BTC")], S[("ETHUSD", 10, "neto ETH")]
cart = pd.concat([bt, et], axis=1, sort=True).mean(axis=1)
cart2 = pd.concat([S[("BTCUSD", 10, "neto BTC x2")], S[("ETHUSD", 10, "neto ETH x2")]], axis=1, sort=True).mean(axis=1)
exc = pd.concat([S[("BTCUSD", 10, "exceso sobre placebo")], S[("ETHUSD", 10, "exceso sobre placebo")]], axis=1, sort=True).mean(axis=1)
p = cart["2021-03-01":]; mitad = p.index[len(p) // 2]
print("\nPRINCIPAL cartera BTC+ETH estándar 2021-03→2026-11: días", len(p), "R/día", round(p.mean(), 3), "t", round(t(p), 2),
      "| 1ª mitad", round(p[:mitad].mean(), 3), "2ª mitad", round(p[mitad:].mean(), 3),
      "| costes x2", round(cart2["2021-03-01":].mean(), 3), "t", round(t(cart2["2021-03-01":]), 2),
      "| exceso placebo", round(exc["2021-03-01":].mean(), 3), "t", round(t(exc["2021-03-01":]), 2))
print("corr BTC-ETH", round(pd.concat([bt, et], axis=1, sort=True).dropna().corr().iloc[0, 1], 2))
j = pd.concat([cart, orb], axis=1, join="inner", sort=True).dropna(); print("corr diaria cartera cripto vs ORB US100 v018:", round(j.corr().iloc[0, 1], 3), len(j), "días")
cart.rename("R").to_frame().to_csv(B + "metodo/v3/cripto_cartera_diaria.csv")
