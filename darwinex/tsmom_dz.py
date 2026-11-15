"""Pruebas B (momentum de series temporales) y C (cesta siempre comprada) del PREREGISTRO_DZ.md.
Uso: python darwinex/tsmom_dz.py <carpeta con datos_tendencia y datos_macro> <serie_v018_be.csv>"""
import sys, os, numpy as np, pandas as pd
RAIZ, ORB = sys.argv[1], sys.argv[2]
DAT, FRED = os.path.join(RAIZ, "datos_tendencia"), os.path.join(RAIZ, "datos_macro", "fred")
IDX = {"US500": ("USD", .018), "US100": ("USD", .018), "US30": ("USD", .018), "US2000": ("USD", .018),
       "GER40": ("EUR", .03), "FRA40": ("EUR", .03), "EU50": ("EUR", .03), "UK100": ("GBP", .035),
       "JP225": ("JPY", .018), "AUS200": ("AUD", .04), "HK50": ("USD", .03)}
FX = ["AUDJPY", "AUDUSD", "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
MET = ["XAUUSD", "XAGUSD", "XPTUSD"]
COD = {"EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N", "JPY": "IR3TIB01JPM156N", "AUD": "IR3TIB01AUM156N",
       "CAD": "IR3TIB01CAM156N", "CHF": "IR3TIB01CHM156N", "NZD": "IR3TIB01NZM156N", "USD": "DFF"}
dias = pd.bdate_range("2003-01-01", "2026-10-30")
def tipo(c):
    d = pd.read_csv(os.path.join(FRED, COD[c] + ".csv")); d.columns = ["d", "v"]
    s = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()
    return s.reindex(pd.date_range("1990-01-01", "2026-12-31")).ffill().reindex(dias).bfill() / 100
R = {c: tipo(c) for c in COD}
def ret(s):
    d = pd.read_csv(os.path.join(DAT, s + ".csv"), index_col=0, parse_dates=True)
    c = pd.to_numeric(d["Close"], errors="coerce").dropna(); c = c[c > 0]
    r = c.pct_change().reindex(dias)
    return r.where(r.abs() < 0.25)
rets = {}
for s, (ccy, div) in IDX.items(): rets[s] = ret(s) - (R[ccy] - div) / 252
for p in FX: rets[p] = ret(p) + (R[p[:3]] - R[p[3:]]) / 252
for m in MET: rets[m] = ret(m) - R["USD"] / 252
X = pd.DataFrame(rets)
vol = np.sqrt((X ** 2).ewm(span=60, min_periods=40).mean() * 252)
px = (1 + X.fillna(0)).cumprod().where(X.notna())
mom = px / px.shift(252) - 1
fin_mes = X.index.to_series().groupby(X.index.to_period("M")).last().values
def cartera(senal_siempre_largo):
    sig = np.sign(mom) if not senal_siempre_largo else (mom * 0 + 1)
    w = (0.10 / vol) * sig
    n = w.notna().sum(axis=1).replace(0, np.nan)
    w = w.div(n, axis=0)
    fm = pd.Series(w.index.isin(fin_mes), w.index)
    w = w[fm].reindex(w.index).ffill().shift(1)        # decidido al cierre de mes, aplicado después
    bruto = (w * X).sum(axis=1, min_count=1)
    rv = bruto.rolling(252, min_periods=200).std() * np.sqrt(252)
    k = (0.10 / rv).clip(upper=3)[fm].reindex(rv.index).ffill().shift(1)
    wk = w.mul(k, axis=0)
    giro = wk.diff().abs().sum(axis=1)
    bruto = (wk * X).sum(axis=1)
    coste = giro * 0.0002 + wk.abs().sum(axis=1) * 0.002 / 252
    return bruto, coste
def stats(r, nombre):
    r = r["2005":"2026-10"]
    m = r.resample("ME").sum()
    sr = m.mean() / m.std() * np.sqrt(12); t = sr * np.sqrt(len(m) / 12)
    h = len(m) // 2
    print(f"{nombre:42s} ret/año {m.mean()*12*100:6.2f} %  vol {m.std()*np.sqrt(12)*100:5.2f} %  SR {sr:5.2f}  t {t:5.2f}"
          f"  1ª mitad {m[:h].mean()*1200:5.2f} %  2ª {m[h:].mean()*1200:5.2f} %")
    return m
bB, cB = cartera(False); bC, cC = cartera(True)
print("Prueba B: momentum 12 m multiactivo (", X.shape[1], "mercados )")
mB = stats(bB - cB, "B neto"); stats(bB - 2 * cB, "B neto costes x2"); stats(bB, "B bruto")
print("Prueba C: cesta siempre comprada (mismas ponderaciones)")
mC = stats(bC - cC, "C neto (placebo de B)")
ex = (mB - mC); t = ex.mean() / ex.std() * np.sqrt(len(ex))
print(f"B − C exceso {ex.mean()*1200:.2f} %/año t {t:.2f}")
por_año = pd.DataFrame({"B": mB, "C": mC}).groupby(mB.index.year).sum().mul(100).round(1)
print(por_año.T.to_string())
# Mezcla con el ORB US100 (2018-26), igual riesgo mensual
o = pd.read_csv(ORB, parse_dates=["d"]).set_index("d").Rbe.resample("ME").sum()
for nm, m in [("B", mB), ("C", mC)]:
    j = pd.concat([o, m], axis=1, keys=["o", "x"], sort=True).dropna()
    so = j.o.mean() / j.o.std() * np.sqrt(12); sx = j.x.mean() / j.x.std() * np.sqrt(12)
    mix = j.o / j.o.std() + j.x / j.x.std(); sm = mix.mean() / mix.std() * np.sqrt(12)
    best = max(((a, ((a * j.o / j.o.std() + (1 - a) * j.x / j.x.std()).mean() /
                     (a * j.o / j.o.std() + (1 - a) * j.x / j.x.std()).std() * np.sqrt(12))) for a in np.linspace(0, 1, 21)), key=lambda z: z[1])
    print(f"ORB 2018-26 SR {so:.2f} | {nm} SR {sx:.2f} corr {j.corr().iloc[0,1]:.2f} | mezcla igual riesgo {sm:.2f} | mejor peso ORB {best[0]:.2f} → SR {best[1]:.2f}")
