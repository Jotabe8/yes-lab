# Ruptura intradía tras día estrecho (preregistro en PREREGISTRO.md). Uso: python3 nr7.py [--oos]
import sys, os, numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "..", "datos_tendencia")
SPR = {**{s: 0.0002 for s in "US500 US100 US30 US2000".split()},
       **{s: 0.0004 for s in "GER40 FRA40 EU50 SPA35 NLD25 UK100 JP225 HK50 AUS200".split()},
       "XAUUSD": 0.0003, "XAGUSD": 0.0010, "WTI": 0.0006, "BRENT": 0.0006, "COPPER": 0.0010}
DESL = 0.0002
INI, FIN, OOS = "2000-01-01", "2022-12-31", "2023-01-01"
VER_OOS = "--oos" in sys.argv


def cargar(s):
    d = pd.read_csv(os.path.join(DATOS, s + ".csv"), index_col=0, parse_dates=True)
    d.columns = [x.lower() for x in d.columns]
    d = d[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()
    d = d[(d.close > 0) & (d.high > d.low) & (d.index.weekday < 5)]
    return d[(d.open >= d.low) & (d.open <= d.high)]


def operar(d, s):
    """Una operación por día con la mecánica de ruptura del rango de ayer. Devuelve R bruta y coste."""
    pH, pL = d.high.shift(1), d.low.shift(1)
    o, h, l, c = d.open, d.high, d.low, d.close
    largo_gap, corto_gap = o > pH, o < pL
    toca_h, toca_l = h >= pH, l <= pL
    ent = np.where(largo_gap, o, np.where(corto_gap, o, np.nan))
    lado = np.where(largo_gap, 1, np.where(corto_gap, -1, 0))
    # dentro del rango al abrir: se activa el extremo que se toque; si se tocan los dos, peor caso
    dentro = ~largo_gap & ~corto_gap
    ambos = dentro & toca_h & toca_l
    solo_h = dentro & toca_h & ~toca_l
    solo_l = dentro & toca_l & ~toca_h
    ent = np.where(solo_h | ambos, pH, np.where(solo_l, pL, ent))
    lado = np.where(solo_h | ambos, 1, np.where(solo_l, -1, lado))
    stop = np.where(lado == 1, pL, pH)
    riesgo = np.abs(ent - stop)
    # salida: stop si se toca (en los huecos ya está fuera, el stop es el otro extremo), si no al cierre
    stop_tocado = np.where(lado == 1, l <= stop, h >= stop) | ambos
    sal = np.where(stop_tocado, stop, c)
    r = np.where(lado != 0, lado * (sal - ent) / riesgo, np.nan)
    coste = (SPR[s] + DESL) * ent / riesgo
    return pd.DataFrame({"r_bruto": r, "coste_r": coste, "mercado": s}, d.index)


def t(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else 0.0


rng = np.random.default_rng(5)
D = {s: cargar(s) for s in SPR}
filas = []
for var in ("NR7", "NR4", "interior"):
    todas = []
    for s, d in D.items():
        rg = d.high - d.low
        if var == "NR7":
            f = rg == rg.rolling(7).min()
        elif var == "NR4":
            f = rg == rg.rolling(4).min()
        else:
            f = (d.high < d.high.shift(1)) & (d.low > d.low.shift(1))
        x = operar(d, s).assign(senal=f.shift(1, fill_value=False).astype(bool).values)
        todas.append(x.dropna(subset=["r_bruto"]))
    A = pd.concat(todas)
    A = A[np.isfinite(A.r_bruto) & (A.coste_r < 1)]
    fit = A[(A.index >= INI) & (A.index <= FIN)]
    v, nv = fit[fit.senal], fit[~fit.senal]
    cnt = v.groupby("mercado").size()
    grupos = {m: g.r_bruto.values for m, g in nv.groupby("mercado")}
    pb = np.array([np.concatenate([rng.choice(grupos[m], n, replace=False) for m, n in cnt.items()]).mean()
                   for _ in range(500)])
    neto = v.r_bruto - v.coste_r
    pm = neto.groupby(v.mercado).mean()
    fila = dict(var=var, ops=len(v), ops_año=len(v) / 23, bruto=v.r_bruto.mean(), coste=v.coste_r.mean(),
                neto=neto.mean(), t_neto=t(neto), resto_dias=nv.r_bruto.mean(), placebo_p95=np.percentile(pb, 95),
                mercados_pos=f"{(pm > 0).sum()}/{len(pm)}", años_pos=(neto.groupby(v.index.year).mean() > 0).mean(),
                neto_x2=(v.r_bruto - 2 * v.coste_r).mean())
    if VER_OOS:
        o = A[(A.index >= OOS) & A.senal]; no = o.r_bruto - o.coste_r
        fila.update(oos_ops=len(o), oos_bruto=o.r_bruto.mean(), oos_neto=no.mean(), oos_t=t(no))
    filas.append(fila)
    print(f"\n{var} neto por mercado:", pm.round(3).to_dict())
T = pd.DataFrame(filas)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("\n", T.round(3).to_string(index=False))
T.to_csv(os.path.join(AQUI, "resultado_oos.csv" if VER_OOS else "resultado_ajuste.csv"), index=False)
