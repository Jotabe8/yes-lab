"""Candidato 1 de la búsqueda v3 (clase B: señal bruta real que el coste del CFD anula).
Pregunta de lugar, no de señal: ¿el ORB de la apertura de NY en BTC/ETH es neto positivo en los
futuros de CME que ofrece FTMO Futures (MBT, BTC, MET, ETH)?

Preregistro (13-11-2026, antes de calcular el neto en futuros): variante principal = la réplica ya
preregistrada (rango 10 min). Los rangos 15/30/60 solo informativos. Pasa si, en el lugar más barato
operable, neto 2018-2026 t >= 2,4 y neto > 0 en 2018-22 y en 2023-26, con costes x2 > 0.
Datos: orb_acciones/orb_cripto (M1 bid/ask Dukascopy, stop 0,15 ATR de sesión, salida 15:55).
Precio del día: cierre diario de docs/data (btc.json / eth.json) del día anterior.
Costes ida y vuelta por contrato (USD): tasa CME no miembro (tabla IBKR 13-11-2026) + comisión FTMO
(0,20 micros / 0,50 estándar por lado) + NFA 0,02 por lado + 1 tick de deslizamiento total.
"""
import glob, json, numpy as np, pandas as pd
B = "/home/user/yes-lab/"
CONTRATOS = {  # símbolo: (activo, tamaño, tasa CME/lado, comisión FTMO/lado, valor de 1 tick en USD)
    "MBT": ("BTCUSD", 0.1, 1.15, 0.20, 0.50),
    "BTC": ("BTCUSD", 5.0, 8.25, 0.50, 25.0),
    "MET": ("ETHUSD", 0.1, 0.10, 0.20, 0.05),
    "ETH": ("ETHUSD", 50.0, 6.05, 0.50, 12.5),
}
CFD_FTMO = 0.00065    # comisión cripto FTMO ida y vuelta (0,0325 % por lado), el spread ya va en r

def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan

def precio(activo):
    j = json.load(open(B + f"docs/data/{'btc' if activo == 'BTCUSD' else 'eth'}.json"))
    s = pd.Series({pd.Timestamp(x["d"]): x["c"] for x in j}).sort_index()
    return s

orb = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
filas, series = [], {}
for activo in ("BTCUSD", "ETHUSD"):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(B + f"orb_acciones/orb_cripto/var_{activo}_*.csv")))
    d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index()
    d = d[d.index.dayofweek < 5]
    px = precio(activo).shift(1).reindex(d.index, method="ffill")
    for L in (10, 15, 30, 60):
        r, spr, lado = d[f"r{L}"], d[f"spr{L}"], d[f"lado{L}"]
        ok = r.notna() & px.notna()
        dist = 0.15 * d.atr                      # stop en USD por unidad de activo
        bruto = (r + spr)[ok]
        lugares = {"Dukascopy (spread real)": r[ok],
                   "CFD FTMO (spread + 0,065 %)": (r - CFD_FTMO * px / dist)[ok]}
        for sym, (act, tam, tasa, com, tick) in CONTRATOS.items():
            if act != activo: continue
            coste_usd = 2 * (tasa + com + 0.02) + tick
            lugares[f"Futuro {sym}"] = (bruto - (coste_usd / tam) / dist[ok])
            lugares[f"Futuro {sym} costes x2"] = (bruto - 2 * (coste_usd / tam) / dist[ok])
        lugares["Bruto (sin coste)"] = bruto
        for nom, x in lugares.items():
            series[(activo, L, nom)] = x
            for per, m in (("2018-22", x.index.year <= 2022), ("2023-26", x.index.year >= 2023),
                           ("2024-26", x.index.year >= 2024), ("2018-26", x.index.year >= 0)):
                y = x[m]
                filas.append(dict(activo=activo, rango=L, lugar=nom, periodo=per, ops=len(y),
                                  R_op=y.mean(), t=t(y)))
        # riesgo por contrato y tamaño de stop, informativo
        if L == 10:
            info = pd.DataFrame({"precio": px, "stop_usd": dist}).loc["2025":]
            print(activo, "2025-26: precio medio", round(info.precio.mean()), "stop medio", round(info.stop_usd.mean(), 1),
                  f"({info.stop_usd.mean()/info.precio.mean()*100:.2f} % del precio)")
res = pd.DataFrame(filas)
res.to_csv(B + "metodo/v3/cripto_futuros.csv", index=False)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 300)
p = res[res.rango == 10].pivot_table(index=["activo", "lugar"], columns="periodo", values=["R_op", "t"]).round(3)
print(p.to_string())
print("\nInformativo, rangos 15/30/60, futuro más barato (BTC estándar / ETH estándar), 2018-26 y 2023-26:")
q = res[(res.rango != 10) & (res.lugar.isin(["Futuro BTC", "Futuro ETH", "Bruto (sin coste)"])) & res.periodo.isin(["2018-26", "2023-26"])]
print(q.pivot_table(index=["activo", "rango", "lugar"], columns="periodo", values=["R_op", "t"]).round(3).to_string())
# correlación diaria con el ORB US100 real y cartera BTC+ETH
for activo in ("BTCUSD", "ETHUSD"):
    x = series[(activo, 10, f"Futuro {'BTC' if activo=='BTCUSD' else 'ETH'}")]
    j = pd.concat([x, orb], axis=1, join="inner").dropna()
    print(activo, "corr diaria con ORB US100 v018:", round(j.iloc[:, 0].corr(j.iloc[:, 1]), 3), "días", len(j))
bt, et = series[("BTCUSD", 10, "Futuro BTC")], series[("ETHUSD", 10, "Futuro ETH")]
j = pd.concat([bt, et], axis=1).dropna(); print("corr BTC-ETH", round(j.corr().iloc[0, 1], 2))
c = pd.concat([bt, et], axis=1).mean(axis=1)
for per, m in (("2018-22", c.index.year <= 2022), ("2023-26", c.index.year >= 2023), ("2018-26", c.index.year > 0)):
    print("cartera BTC+ETH estándar media diaria", per, round(c[m].mean(), 3), "t", round(t(c[m]), 2))
