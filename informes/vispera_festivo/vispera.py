# Víspera de festivo en índices (preregistro en PREREGISTRO.md). Uso: python3 vispera.py [--oos]
import sys, os, numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "..", "datos_tendencia")
IDX = "US500 US100 US30 US2000 GER40 FRA40 EU50 SPA35 NLD25 UK100 JP225 HK50 AUS200".split()
USA = {"US500", "US100", "US30", "US2000"}
INI, FIN, OOS = "2000-01-01", "2022-12-31", "2023-01-01"
VER_OOS = "--oos" in sys.argv


def cargar(s):
    d = pd.read_csv(os.path.join(DATOS, s + ".csv"), index_col=0, parse_dates=True)
    d.columns = [x.lower() for x in d.columns]
    d = d[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()
    d = d[(d.close > 0) & (d.high > d.low) & (d.index.weekday < 5)]   # fuera días planos (festivos con fila)
    d = d[(d.open >= d.low) & (d.open <= d.high)]
    tr = np.maximum(d.high - d.low, np.maximum(abs(d.high - d.close.shift()), abs(d.low - d.close.shift())))
    d["atr"] = tr.rolling(20).mean().shift(1)        # ATR conocido al abrir
    d["prev"] = d.close.shift(1)
    sig = pd.Series(d.index[1:].tolist() + [pd.NaT], d.index)
    lab = np.busday_count(d.index.values.astype("datetime64[D]"),
                          sig.fillna(d.index[-1]).values.astype("datetime64[D]"))
    d["vispera"] = (lab > 1) & sig.notna().values      # el siguiente día laborable no se negocia
    d["spr"] = 0.0002 if s in USA else 0.0004
    return d.dropna(subset=["atr", "prev"])


def r_ops(d, var, stop):
    if var == "A":
        g = d.close - d.open
        if stop:
            g = np.where(d.low <= d.open - d.atr, -d.atr, g)
        c = d.spr * d.open
    else:
        g = d.close - d.prev
        c = d.spr * d.prev + (0.04 + 0.065) / 365 * d.prev    # una noche a tipo medio + recargo FTMO
    return pd.DataFrame({"r_bruto": np.asarray(g) / d.atr.values, "coste_r": np.asarray(c) / d.atr.values}, d.index)


def t(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else 0.0


D = {s: cargar(s) for s in IDX}
rng = np.random.default_rng(11)
filas = []
for var, stop in [("A", False), ("A", True), ("B", False)]:
    ops, pl, por = [], [], {}
    for s, d in D.items():
        r = r_ops(d, var, stop).assign(mercado=s, vispera=d.vispera)
        ops.append(r)
    ops = pd.concat(ops)
    fit = ops[(ops.index >= INI) & (ops.index <= FIN)]
    v = fit[fit.vispera]; normal = fit[~fit.vispera]
    # placebo: mismo nº de días normales al azar por mercado
    cnt = v.groupby("mercado").size()
    grupos = {m: g.r_bruto.values for m, g in normal.groupby("mercado")}
    pb = np.array([np.concatenate([rng.choice(grupos[m], n, replace=False) for m, n in cnt.items()]).mean()
                   for _ in range(500)])
    pm = v.groupby("mercado").r_bruto.mean()
    neto = v.r_bruto - v.coste_r
    fila = dict(var=var + (" stop 1 ATR" if stop else ""), ops=len(v), ops_año=len(v) / 23, bruto=v.r_bruto.mean(),
                coste=v.coste_r.mean(), neto=neto.mean(), t_neto=t(neto), normal=normal.r_bruto.mean(),
                placebo_p95=np.percentile(pb, 95), mercados_pos=f"{(pm > 0).sum()}/{len(pm)}",
                años_pos=(neto.groupby(v.index.year).mean() > 0).mean(),
                neto_x2=(v.r_bruto - 2 * v.coste_r).mean())
    if VER_OOS:
        o = ops[(ops.index >= OOS) & ops.vispera]; no = o.r_bruto - o.coste_r
        fila.update(oos_ops=len(o), oos_bruto=o.r_bruto.mean(), oos_neto=no.mean(), oos_t=t(no),
                    oos_normal=ops[(ops.index >= OOS) & ~ops.vispera].r_bruto.mean())
    filas.append(fila)
    print(f"\n{fila['var']}: bruto por mercado\n", pm.round(3).to_string())
    print("por año (neto):", neto.groupby(v.index.year).mean().round(2).tolist())
T = pd.DataFrame(filas)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("\n", T.round(3).to_string(index=False))
T.to_csv(os.path.join(AQUI, "resultado_oos.csv" if VER_OOS else "resultado_ajuste.csv"), index=False)
