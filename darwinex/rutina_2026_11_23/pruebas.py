"""Rutina 23-11-2026: las dos pruebas de PREREGISTRO.md.

A. Corto del 10 años las 5 primeras sesiones si la bolsa batió a los bonos en las 15 primeras del mes anterior.
B. Tendencia EWMA 20/80 en ZT, ZF, ZN y ZB (tick grande) frente a ES.

Uso: python -m darwinex.rutina_2026_11_23.pruebas
"""
import os
import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..", "datos_bonos")
COSTE_A = 3.0  # pb por operación
TICK_PB = {"ZT": 0.4, "ZF": 0.7, "ZN": 1.5, "ZB": 2.7, "ES": 0.5}
FRED_DE = {"ZT": "DGS2", "ZF": "DGS5", "ZN": "DGS10", "ZB": "DGS30", "ES": None}


def fred(s):
    d = pd.read_csv(os.path.join(D, s + ".csv")); d.columns = ["d", "v"]
    return pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna()


def ret_fred(serie, dur):
    y = fred(serie)
    return (-dur * y.diff() / 100 + y.shift(1) / 100 / 252).dropna()


def precio(sym):
    d = pd.read_csv(os.path.join(D, sym + ".csv"), parse_dates=["Date"]).set_index("Date")["Close"]
    return d[~d.index.duplicated()].dropna()


def t(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan


# ---------------------------------------------------------------- A
def prueba_a():
    rb = ret_fred("DGS10", 8.5)
    sp = precio("GSPC").pct_change()
    df = pd.concat([rb.rename("b"), sp.rename("s")], axis=1, sort=True).dropna()
    df["m"] = df.index.to_period("M")
    meses = sorted(df.m.unique())
    filas = []
    for i in range(len(meses) - 1):
        a, b = df[df.m == meses[i]], df[df.m == meses[i + 1]]
        if len(a) < 15 or len(b) < 10:
            continue
        sig = (1 + a.s.iloc[:15]).prod() - (1 + a.b.iloc[:15]).prod()
        corto = -((1 + b.b.iloc[:5]).prod() - 1) * 1e4
        placebo = -((1 + b.b.iloc[5:10]).prod() - 1) * 1e4
        filas.append(dict(mes=meses[i + 1].to_timestamp(), sig=sig > 0, bruto=corto, placebo=placebo))
    r = pd.DataFrame(filas).set_index("mes")
    op = r[r.sig].copy()
    op["neto"] = op.bruto - COSTE_A
    op["neto2"] = op.bruto - 2 * COSTE_A
    op["pla_neto"] = op.placebo - COSTE_A
    fuera = op[(op.index < "2002-08-01") | (op.index >= "2025-07-01")]
    publ = op[(op.index >= "2002-08-01") & (op.index < "2025-07-01")]
    out = ["A. Corto del 10 años 5 primeras sesiones si S&P > bono en las 15 primeras del mes anterior (pb/op)"]
    def lin(nombre, x, col="neto"):
        return f"  {nombre:<34} n={len(x):4d}  neto {x[col].mean():+6.1f}  t {t(x[col]):+5.2f}  bruto {x.bruto.mean():+6.1f}"
    out += [lin("Completo 1990-2026", op), lin("Fuera de muestra (90-02 y 25-26)", fuera),
            lin("Tramo publicado 2002-08 a 2025-06", publ),
            f"  {'Completo, costes x2':<34} neto {op.neto2.mean():+6.1f}  t {t(op.neto2):+5.2f}",
            f"  {'Placebo sesiones 6-10, completo':<34} neto {op.pla_neto.mean():+6.1f}  t {t(op.pla_neto):+5.2f}",
            f"  {'Placebo fuera de muestra':<34} neto {fuera.pla_neto.mean():+6.1f}  t {t(fuera.pla_neto):+5.2f}"]
    no = r[~r.sig]
    out.append(f"  {'Informativo: meses sin señal':<34} n={len(no):4d}  bruto corto {no.bruto.mean():+6.1f}  t {t(no.bruto):+5.2f}")
    for desde, hasta in [("1990", "1999"), ("2000", "2009"), ("2010", "2018"), ("2019", "2026")]:
        x = op.loc[desde:hasta]
        out.append(f"  {desde}-{hasta}: n={len(x):3d} neto {x.neto.mean():+6.1f} t {t(x.neto):+5.2f}")
    ok = (fuera.neto.mean() > 0 and t(fuera.neto) >= 2.0 and t(op.neto) >= 2.4 and op.neto2.mean() > 0
          and op.pla_neto.mean() < op.neto.mean())
    out.append(f"  Veredicto A: {'PASA' if ok else 'NO PASA'}")
    return out


# ---------------------------------------------------------------- B
def retornos_futuro(sym):
    p = precio(sym)
    r = p.pct_change().dropna()
    if FRED_DE[sym] is None:
        return r[r.abs() < 0.12], 0
    rf = fred(FRED_DE[sym]).diff().reindex(r.index)  # Δy en puntos
    df = pd.concat([r.rename("f"), rf.rename("dy")], axis=1, sort=True).dropna()
    beta = np.polyfit(df.dy, df.f, 1)[0]
    res = df.f - beta * df.dy
    salto = res.abs() > 4 * res.std()
    r = r.copy()
    r.loc[salto[salto].index] = beta * df.dy[salto]
    return r, int(salto.sum())


def tendencia(r, tau, tick_pb, k=1.0):
    lp = np.log1p(r).cumsum()
    vol = r.rolling(60).std()
    s = (lp.ewm(span=tau).mean() - lp.ewm(span=4 * tau).mean()) / vol
    s = (s / s.rolling(250).std()).clip(-2, 2)
    pos = (s / (vol * np.sqrt(252))).shift(1) * 0.10  # 10% de vol objetivo por contrato
    bruto = pos * r
    coste = pos.diff().abs() * tick_pb / 1e4 * k
    return (bruto - coste).dropna(), bruto.dropna()


def sharpe(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(252)


def prueba_b():
    rets, saltos = {}, {}
    for s in TICK_PB:
        rets[s], saltos[s] = retornos_futuro(s)
    out = ["B. Tendencia EWMA 20/80 en Treasuries (tick grande) frente a ES",
           "  Saltos de vencimiento sustituidos: " + ", ".join(f"{s} {saltos[s]}" for s in TICK_PB)]
    res = {}
    for tau in (5, 10, 20, 50):
        netos, netos2 = {}, {}
        for s in TICK_PB:
            netos[s], _ = tendencia(rets[s], tau, TICK_PB[s])
            netos2[s], _ = tendencia(rets[s], tau, TICK_PB[s], k=2.0)
        cart = pd.concat([netos[s] for s in ("ZT", "ZF", "ZN", "ZB")], axis=1, sort=True).mean(axis=1, skipna=False).dropna()
        cart2 = pd.concat([netos2[s] for s in ("ZT", "ZF", "ZN", "ZB")], axis=1, sort=True).mean(axis=1, skipna=False).dropna()
        res[tau] = (cart, cart2, netos)
    cart, cart2, netos = res[20]
    p = cart.loc["2009-07":"2026-10"]
    mitad = p.index[len(p) // 2]
    n_años = len(p) / 252
    sr = sharpe(p)
    t_p = sr * np.sqrt(n_años)
    def l(nombre, x):
        x = x.dropna()
        return f"  {nombre:<36} Sharpe {sharpe(x):+5.2f}  t {sharpe(x) * np.sqrt(len(x) / 252):+5.2f}"
    out += [l("Cartera τ=20, 2009-07 a 2026-10", p),
            l("  1.ª mitad", p.loc[:mitad]), l("  2.ª mitad", p.loc[mitad:]),
            l("  2019-2026", p.loc["2019":]),
            l("  costes x2", cart2.loc["2009-07":"2026-10"]),
            l("Informativo 2001 a 2009-06", cart.loc[:"2009-06"])]
    for s in TICK_PB:
        out.append(l(f"  {s} solo, 2009-07 a 2026-10", netos[s].loc["2009-07":"2026-10"]))
    es = netos["ES"].loc["2009-07":"2026-10"]
    out.append("  Informativo, otras τ (cartera, 2009-07 a 2026-10 / 2001 a 2009-06):")
    for tau in (5, 10, 50):
        c = res[tau][0]
        out.append(f"    τ={tau:<3} Sharpe {sharpe(c.loc['2009-07':]):+5.2f} / {sharpe(c.loc[:'2009-06']):+5.2f}")
    ok = (t_p >= 2.4 and p.loc[mitad:].mean() > 0 and p.loc["2019":].mean() > 0
          and cart2.loc["2009-07":"2026-10"].mean() > 0 and sr > sharpe(es))
    out.append(f"  Veredicto B: {'PASA' if ok else 'NO PASA'}")
    return out


if __name__ == "__main__":
    print("\n".join(prueba_a() + [""] + prueba_b()))
