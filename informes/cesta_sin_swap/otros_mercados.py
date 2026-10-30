# La misma cesta (SMA200, pesos inversos a la volatilidad, vol objetivo) en otros mercados, un año FTMO 2-Step 100K.
# Swap aproximado: metales/cripto pagan tipo USD + recargo; forex paga/cobra el diferencial ± 2 %.
import os, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import importlib.util
spec = importlib.util.spec_from_file_location("f", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ftmo_1anio.py"))
src = open(spec.origin).read().split("filas = []")[0]
g = {"__file__": spec.origin}; exec(src, g)
anio, mc, tip_base = g["anio"], g["mc"], g["tip"]
RAIZ = os.path.join(os.path.dirname(spec.origin), "..", "..")
fred = {"AUD": "IR3TIB01AUM156N", "CAD": "IR3TIB01CAM156N", "NZD": "IR3TIB01NZM156N", "CHF": "IR3TIB01CHM156N"}

CESTAS = {
    "oro": (["XAUUSD"], "largo", 0.04),
    "metales": (["XAUUSD", "XAGUSD", "XPTUSD", "COPPER"], "largo", 0.04),
    "forex 11 pares (largo/corto)": ("EURUSD GBPUSD USDJPY AUDUSD USDCAD NZDUSD USDCHF EURJPY GBPJPY AUDJPY EURGBP".split(), "ambos", 0.02),
    "cripto BTC+ETH": (["BTCUSD", "ETHUSD"], "largo", 0.20),
    "índices + metales": (["US500", "US100", "US30", "GER40", "UK100", "JP225", "XAUUSD", "XAGUSD"], "largo", 0.055),
}
CCY = {"US500": "USD", "US100": "USD", "US30": "USD", "GER40": "EUR", "UK100": "GBP", "JP225": "JPY"}


def cargar(lista):
    cl = pd.concat({s: pd.read_csv(os.path.join(RAIZ, "datos_tendencia", s + ".csv"), index_col=0, parse_dates=True)["Close"]
                    for s in lista}, axis=1, sort=True)
    cl = cl[cl.index.weekday < 5].ffill().loc["2003-01-01":]
    return cl


def tasa(cl):
    t = {}
    for k, f in {**{"USD": "DFF", "EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N", "JPY": "IR3TIB01JPM156N"}, **fred}.items():
        d = pd.read_csv(os.path.join(RAIZ, "datos_macro", "fred", f + ".csv")); d.columns = ["d", "v"]
        s = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna() / 100
        t[k] = s.reindex(cl.index, method="ffill").bfill()
    return t


def serie(lista, modo, recargo, vol_obj, swap):
    cl = cargar(lista); ret = cl.pct_change().fillna(0)
    lado = np.sign(cl - cl.rolling(200).mean()).shift(1).fillna(0)
    if modo == "largo": lado = lado.clip(lower=0)
    vol = ret.rolling(60).std().shift(1) * np.sqrt(252)
    w = (lado / vol).fillna(0) / len(lista)
    pv = (w * ret).sum(axis=1).rolling(60).std().shift(1) * np.sqrt(252)
    w = w.mul((vol_obj / pv).clip(upper=8).fillna(0), axis=0)
    w = w.clip(-15 / len(lista), 15 / len(lista))
    r = (w * ret).sum(axis=1) - 0.0004 * w.diff().abs().sum(axis=1)
    if swap:
        t = tasa(cl); gap = pd.Series(np.r_[1, np.diff(cl.index.values).astype("timedelta64[D]").astype(float)], cl.index)
        coste = pd.DataFrame(0.0, cl.index, cl.columns)
        for s in lista:
            wl = w[s].shift(1).fillna(0)
            if len(s) == 6 and s[:3] in t and s[3:] in t:           # par: largo base paga cotizada - base
                dif = t[s[3:]] - t[s[:3]]
                coste[s] = wl * dif + wl.abs() * recargo
            else:
                r0 = t[CCY.get(s, "USD")] if not s.endswith(("BTCUSD", "ETHUSD")) else 0
                coste[s] = wl * r0 + wl.abs() * recargo
        r -= coste.sum(axis=1) / 365 * gap
    return r.loc["2005-01-01":].loc[lambda x: x.index >= cl.dropna().index[0] + pd.Timedelta(days=300)]


filas = []
for nom, (lista, modo, rec) in CESTAS.items():
    for v in (0.15, 0.20):
        for swap in (True, False):
            r = serie(lista, modo, rec, v, swap)
            for sn, x in (("cesta", r), ("control", r - r.mean())):
                filas.append(dict(cesta=nom, vol=v, swap="FTMO aprox" if swap else "sin swap", serie=sn,
                                  desde=r.index[0].year, rend_anual=x.mean() * 252, **mc(x, True, n=3000)))
T = pd.DataFrame(filas)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(T.round(3).to_string(index=False)); T.to_csv("otros_mercados.csv", index=False)
