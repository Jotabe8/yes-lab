# Tendencia con operaciones largas y trailing stop (preregistro en PREREGISTRO.md).
# Ruptura Donchian N días al cierre, entrada a la apertura siguiente, stop inicial SL ATR(20),
# trailing chandelier TR ATR, sin objetivo. Costes: spread + financiación nocturna con tipos reales.
# Uso: python3 tendencia.py [--oos]   (sin --oos solo se imprime el ajuste 2005-2022)
import sys, os, numpy as np, pandas as pd
from numba import njit

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
DATOS = os.path.join(RAIZ, "datos_tendencia")
FRED = os.path.join(RAIZ, "datos_macro", "fred")
INI, FIN_AJUSTE, INI_OOS = "2005-01-01", "2022-12-31", "2023-01-01"
VER_OOS = "--oos" in sys.argv
ATR_N, SL = 20, 3.0

# mercado: (grupo, divisa (o par base/cotizada), spread ida y vuelta en fracción del precio)
IDX = {"US500": "USD", "US100": "USD", "US30": "USD", "US2000": "USD", "GER40": "EUR", "FRA40": "EUR",
       "EU50": "EUR", "SPA35": "EUR", "NLD25": "EUR", "UK100": "GBP", "JP225": "JPY", "HK50": "USD", "AUS200": "AUD"}
MK = {s: ("indices", ccy, 0.0002 if ccy == "USD" and s != "HK50" else 0.0004) for s, ccy in IDX.items()}
for p in "EURUSD GBPUSD USDJPY AUDUSD USDCAD NZDUSD USDCHF EURJPY GBPJPY AUDJPY EURGBP".split():
    MK[p] = ("forex", (p[:3], p[3:]), 0.00015)
for s, g, c in [("XAUUSD", "metales", 0.0003), ("XAGUSD", "metales", 0.0010), ("XPTUSD", "metales", 0.0015),
                ("COPPER", "metales", 0.0010), ("WTI", "energia", 0.0006), ("BRENT", "energia", 0.0006),
                ("NATGAS", "energia", 0.0020), ("CORN", "agricolas", 0.0015), ("WHEAT", "agricolas", 0.0015),
                ("SOYBEAN", "agricolas", 0.0015), ("COFFEE", "agricolas", 0.0020), ("SUGAR", "agricolas", 0.0020),
                ("COCOA", "agricolas", 0.0020), ("BTCUSD", "cripto", 0.0010), ("ETHUSD", "cripto", 0.0015)]:
    MK[s] = (g, "USD", c)
# recargo anual del broker sobre la financiación: escenario normal y escenario FTMO (índices observados)
RECARGO = {"normal": {"indices": .025, "forex": .01, "metales": .025, "energia": .03, "agricolas": .03, "cripto": .15},
           "ftmo":   {"indices": .065, "forex": .02, "metales": .04, "energia": .05, "agricolas": .05, "cripto": .20}}


def tipos():
    """Tipo a 3 meses por divisa, diario, en fracción anual (FRED/OCDE; USD = fondos federales)."""
    cod = {"USD": "IR3TIB01USM156N", "EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N", "JPY": "IR3TIB01JPM156N",
           "AUD": "IR3TIB01AUM156N", "CAD": "IR3TIB01CAM156N", "NZD": "IR3TIB01NZM156N", "CHF": "IR3TIB01CHM156N"}
    dias = pd.date_range("1998-01-01", "2026-12-31")
    out = {}
    for k, f in cod.items():
        d = pd.read_csv(os.path.join(FRED, f + ".csv"))
        d.columns = ["d", "v"]
        s = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()
        out[k] = s.reindex(dias, method="ffill").bfill() / 100
    d = pd.read_csv(os.path.join(FRED, "DFF.csv")); d.columns = ["d", "v"]
    s = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()
    out["USD"] = s.reindex(dias, method="ffill").bfill() / 100
    return pd.DataFrame(out)


def cargar(s):
    d = pd.read_csv(os.path.join(DATOS, s + ".csv"), index_col=0, parse_dates=True)
    d.columns = [x.lower() for x in d.columns]
    d = d[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()
    d = d[(d.close > 0) & (d.index >= "2003-01-01")]
    # Yahoo a veces da apertura 0 o fuera del rango: se acota al rango de la vela
    d["open"] = d.open.where((d.open >= d.low) & (d.open <= d.high), d.close.shift(1)).clip(d.low, d.high)
    d["high"] = d[["open", "high", "close"]].max(axis=1); d["low"] = d[["open", "low", "close"]].min(axis=1)
    return d


@njit(cache=True)
def sim(o, h, l, c, A, u, gap, finL, finS, spread, TR, t0):
    """u[t] = señal al cierre de t (+1/-1); entrada a o[t+1]. Devuelve operaciones y P&L diario en R."""
    n = len(c)
    ti = np.zeros(n, np.int64); tx = np.zeros(n, np.int64); tg = np.zeros(n); ts = np.zeros(n); tf = np.zeros(n)
    tdir = np.zeros(n); dia = np.zeros(n)
    k = 0; pos = 0; ent = 0.0; risk = 0.0; stop = 0.0; ext = 0.0; mark = 0.0; fin = 0.0; i0 = 0
    for t in range(t0, n):
        if pos == 0 and t > t0 and u[t - 1] != 0 and A[t - 1] > 0:
            pos = int(u[t - 1]); ent = o[t]; risk = SL * A[t - 1]; stop = ent - pos * risk
            ext = ent; mark = ent; fin = 0.0; i0 = t
            dia[t] -= spread * ent / risk
        if pos == 0:
            continue
        salir = (pos == 1 and l[t] <= stop) or (pos == -1 and h[t] >= stop)
        if salir:
            px = min(o[t], stop) if pos == 1 else max(o[t], stop)
            if t == i0:
                px = stop
            dia[t] += pos * (px - mark) / risk
            ti[k] = i0; tx[k] = t; tg[k] = pos * (px - ent) / risk; ts[k] = spread * ent / risk; tf[k] = fin
            tdir[k] = pos; k += 1; pos = 0
            continue
        dia[t] += pos * (c[t] - mark) / risk; mark = c[t]
        if pos == 1:
            ext = max(ext, h[t]); stop = max(stop, ext - TR * A[t])
        else:
            ext = min(ext, l[t]); stop = min(stop, ext + TR * A[t])
        if t + 1 < n:   # financiación de las noches hasta la vela siguiente
            r = finL[t] if pos == 1 else finS[t]
            f = r / 365.0 * gap[t + 1] * c[t] / risk
            fin += f; dia[t] -= f
    return ti[:k], tx[:k], tg[:k], ts[:k], tf[:k], tdir[:k], dia


def preparar():
    R = tipos()
    M = {}
    for s, (g, ccy, spr) in MK.items():
        if not os.path.exists(os.path.join(DATOS, s + ".csv")):
            continue
        d = cargar(s)
        if len(d) < 1500:
            continue
        tr = np.maximum(d.high - d.low, np.maximum(abs(d.high - d.close.shift()), abs(d.low - d.close.shift())))
        A = tr.rolling(ATR_N).mean().fillna(0).values
        rr = R.reindex(d.index, method="ffill")
        if g == "forex":
            dif = (rr[ccy[1]] - rr[ccy[0]]).values           # largo base: paga cotizada, cobra base
            base = {"L": dif, "S": -dif}
        elif g == "cripto":
            base = {"L": np.zeros(len(d)), "S": np.zeros(len(d))}
        else:
            r = rr[ccy].values
            base = {"L": r, "S": -r}
        fins = {e: (base["L"] + RECARGO[e][g], base["S"] + RECARGO[e][g]) for e in RECARGO}
        gap = np.r_[1, np.diff(d.index.values).astype("timedelta64[D]").astype(float)]
        M[s] = dict(g=g, d=d, A=A, gap=gap, fins=fins, spr=spr,
                    t0=int(np.searchsorted(d.index.values, np.datetime64("2004-06-01"))))
    return M


def senal(d, N, solo_largos):
    hh = d.high.rolling(N).max().shift(1); ll = d.low.rolling(N).min().shift(1)
    u = np.where(d.close > hh, 1, np.where(d.close < ll, -1, 0))
    if solo_largos:
        u[u < 0] = 0
    return u.astype(np.float64)


def correr(M, N, TR, solo_largos, esc="normal", placebo_rng=None, nent=None):
    filas, diario = [], {}
    for s, m in M.items():
        d = m["d"]
        if placebo_rng is None:
            u = senal(d, N, solo_largos)
        else:   # mismas salidas, entrada en día y dirección al azar con la misma frecuencia
            p = nent[s] / max(1, len(d) - m["t0"])
            u = (placebo_rng.random(len(d)) < p).astype(np.float64)
            if not solo_largos:
                u *= placebo_rng.choice([-1.0, 1.0], len(d))
        fL, fS = m["fins"][esc]
        ti, tx, tg, ts, tf, tdir, dia = sim(d.open.values, d.high.values, d.low.values, d.close.values, m["A"], u,
                                             m["gap"], fL, fS, m["spr"], TR, m["t0"])
        f = pd.DataFrame({"mercado": s, "grupo": m["g"], "entrada": d.index[ti], "salida": d.index[tx],
                          "dir": tdir, "r_bruto": tg, "c_spread": ts, "c_fin": tf})
        f["dias"] = (f.salida - f.entrada).dt.days
        filas.append(f)
        diario[s] = pd.Series(dia, d.index)
    ops = pd.concat(filas, ignore_index=True)
    ops["r_neto"] = ops.r_bruto - ops.c_spread - ops.c_fin
    return ops, diario


def t_stat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else 0.0


def periodo(ops, a, b):
    return ops[(ops.entrada >= a) & (ops.entrada <= b)]


def resumen(ops, a, b):
    o = periodo(ops, a, b)
    años = (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25
    return dict(ops=len(o), ops_año=len(o) / años, dias=o.dias.mean(), bruto=o.r_bruto.mean(),
                spread=o.c_spread.mean(), fin=o.c_fin.mean(), neto=o.r_neto.mean(), t_neto=t_stat(o.r_neto),
                gan=(o.r_neto > 0).mean())


if __name__ == "__main__":
    M = preparar()
    print("mercados:", len(M), " ".join(M))
    fin_b = FIN_AJUSTE
    filas = []
    for N in (20, 55, 100):
        for TR in (2.0, 3.0, 4.0):
            for sl in (False, True):
                ops, _ = correr(M, N, TR, sl)
                opf, _ = correr(M, N, TR, sl, "ftmo")
                r = resumen(ops, INI, fin_b); rf = resumen(opf, INI, fin_b)
                g = periodo(ops, INI, fin_b).groupby("grupo").r_neto.mean()
                fila = dict(N=N, TR=TR, lados="largos" if sl else "ambos", **r, neto_ftmo=rf["neto"],
                            grupos_pos=int((g > 0).sum()), grupos=len(g))
                if VER_OOS:
                    ro = resumen(ops, INI_OOS, "2026-12-31"); rfo = resumen(opf, INI_OOS, "2026-12-31")
                    fila.update(oos_ops=ro["ops"], oos_bruto=ro["bruto"], oos_neto=ro["neto"], oos_t=ro["t_neto"],
                                oos_neto_ftmo=rfo["neto"])
                filas.append(fila)
    T = pd.DataFrame(filas)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(T.round(3).to_string(index=False))
    T.to_csv(os.path.join(AQUI, "variantes_oos.csv" if VER_OOS else "variantes_ajuste.csv"), index=False)
