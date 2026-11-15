"""Re-pruebas preregistradas (PREREGISTRO.md): gotobi en el yen 2003-26 y deriva EIA en USOIL 2011-26.
Uso: python analisis.py  (lee datos/)"""
import glob, calendar
import numpy as np, pandas as pd

AQUI = __file__.rsplit("/", 1)[0]
rng = np.random.default_rng(7)
T_MIN = 2.64

def t(x):
    x = np.asarray(x, float); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan

def cargar(sim):
    m = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{AQUI}/datos/{sim}_*_m1.csv.gz"))])
    m = m.drop_duplicates("ts").sort_values("ts")
    m.index = pd.to_datetime(m.ts * 60, unit="s", utc=True)
    d1 = pd.concat([pd.read_csv(f, parse_dates=["dia"]) for f in sorted(glob.glob(f"{AQUI}/datos/{sim}_*_d1.csv"))])
    d1 = d1.drop_duplicates("dia").sort_values("dia").set_index("dia")
    return m, d1

def recorrer(tramo, ent, s, dist):
    """salida con stop vela a vela; hueco a la apertura de la vela"""
    stp = ent - s * dist
    toc = (tramo.low.values <= stp) if s > 0 else (tramo.high.values >= stp)
    if toc.any():
        i = np.argmax(toc); o = tramo.open.values[i]
        return min(stp, o) if s > 0 else max(stp, o)
    return tramo.close.values[-1]

# ---------------------------------------------------------------- gotobi
def es_gotobi(fechas):
    """fechas: días laborables (JST). Devuelve conjunto de fechas gotobi movidas al viernes si caen en fin de semana."""
    res = set()
    anios = sorted({f.year for f in fechas})
    for y in anios:
        for mes in range(1, 13):
            ult = calendar.monthrange(y, mes)[1]
            for dd in [5, 10, 15, 20, 25, ult]:
                f = pd.Timestamp(y, mes, dd)
                while f.dayofweek >= 5: f -= pd.Timedelta(days=1)
                res.add(f.date())
    return res

def gotobi(sim, coste_fijo=None):
    m, d1 = cargar(sim)
    rango = (d1.high - d1.low).rolling(14).mean().shift(1)     # conocido antes del día
    jst = m.index + pd.Timedelta(hours=9)
    m = m.assign(jst_dia=jst.date, jst_min=jst.hour * 60 + jst.minute)
    m = m[(m.jst_min >= 480) & (m.jst_min <= 594)]               # 08:00 .. 09:54 JST
    filas = []
    for f, g in m.groupby("jst_dia"):
        if pd.Timestamp(f).dayofweek >= 5: continue
        if g.jst_min.iloc[0] != 480 or g.jst_min.iloc[-1] != 594 or len(g) < 90: continue
        # día de servidor que acaba justo antes: la vela 23:00 UTC es del día de servidor siguiente al cierre NY
        srv = (g.index[0].tz_convert("America/New_York") + pd.Timedelta(hours=7)).normalize().tz_localize(None)
        r = rango.get(srv, np.nan)
        if not r > 0: continue
        dist = 0.25 * r; ent = g.open.iloc[0]
        sal = recorrer(g, ent, 1, dist)
        filas.append(dict(fecha=pd.Timestamp(f), r_bruto=(sal - ent) / dist, spread_pct=g.spread.iloc[0] / ent,
                          dist_pct=dist / ent, pips_bruto=(sal - ent) * 100, dist_pips=dist * 100, precio=ent))
    x = pd.DataFrame(filas)
    x["gotobi"] = x.fecha.dt.date.isin(es_gotobi(x.fecha))
    return x

def resumen_gotobi(sim, x):
    rec = x[x.fecha >= "2023-01-01"]
    spr_hoy = rec.spread_pct.median()
    coste_pct = spr_hoy + 0.00005
    x["coste_r"] = coste_pct / x.dist_pct
    x["coste_r_hist"] = (x.spread_pct + 0.00005) / x.dist_pct
    x["neto"] = x.r_bruto - x.coste_r
    x["neto_x2"] = x.r_bruto - 2 * x.coste_r
    x["neto_hist"] = x.r_bruto - x.coste_r_hist
    gt, ng = x[x.gotobi], x[~x.gotobi]
    nuevo = gt[gt.fecha < "2018-01-01"]; visto = gt[gt.fecha >= "2018-01-01"]
    pl = np.array([ng.r_bruto.sample(len(gt), random_state=int(rng.integers(1e9))).mean() for _ in range(2000)])
    out = dict(sim=sim, ops=len(gt), ops_año=len(gt) / ((gt.fecha.max() - gt.fecha.min()).days / 365.25),
               bruto=gt.r_bruto.mean(), t_bruto=t(gt.r_bruto), pips_bruto=gt.pips_bruto.mean(),
               coste_r=gt.coste_r.mean(), coste_pips=(coste_pct * gt.precio * 100).mean(),
               neto=gt.neto.mean(), t_neto=t(gt.neto), neto_x2=gt.neto_x2.mean(), neto_hist=gt.neto_hist.mean(),
               nuevo_bruto=nuevo.r_bruto.mean(), nuevo_t_bruto=t(nuevo.r_bruto), nuevo_neto=nuevo.neto.mean(),
               visto_bruto=visto.r_bruto.mean(), visto_neto=visto.neto.mean(), visto_t_neto=t(visto.neto),
               otros_dias=ng.r_bruto.mean(), placebo_p95=np.percentile(pl, 95),
               equilibrio_pips=gt.pips_bruto.mean(), spread_hoy_pips=(spr_hoy * gt.precio.iloc[-200:]).mean() * 100)
    por_anio = gt.groupby(gt.fecha.dt.year).agg(bruto=("r_bruto", "mean"), neto=("neto", "mean"), pips=("pips_bruto", "mean"), n=("r_bruto", "size"))
    return out, por_anio

# ---------------------------------------------------------------- EIA
def eia():
    m, d1 = cargar("USOIL")
    tr = pd.concat([d1.high - d1.low, (d1.high - d1.close.shift()).abs(), (d1.low - d1.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    ny = m.index.tz_convert("America/New_York")
    m = m.assign(dia=ny.tz_localize(None).normalize(), mi=ny.hour * 60 + ny.minute, dow=ny.dayofweek)
    filas = []
    for (dia, dow), g in m.groupby(["dia", "dow"]):
        g = g.set_index("mi")
        if not all(k in g.index for k in (630, 634, 869)): continue
        o0, ent = g.at[630, "open"], g.at[634, "close"]
        if ent == o0 or ent <= 0: continue
        s = np.sign(ent - o0)
        tramo = g.loc[635:869]
        if len(tramo) < 200: continue
        srv = dia  # 10:30 NY cae en el día de servidor de esa misma fecha
        a = atr.get(srv, np.nan)
        if not a > 0: continue
        dist = 0.5 * a
        sal = recorrer(tramo, ent, s, dist)
        filas.append(dict(fecha=dia, dow=dow, s=s, r_bruto=s * (sal - ent) / dist, pb=s * (sal / ent - 1) * 1e4,
                          mov=(sal - ent) / dist, coste_r=0.00053 * ent / dist, coste_r_hist=g.at[634, "spread"] / dist))
    x = pd.DataFrame(filas)
    x["neto"] = x.r_bruto - x.coste_r; x["neto_x2"] = x.r_bruto - 2 * x.coste_r; x["neto_hist"] = x.r_bruto - x.coste_r_hist
    return x

def resumen_eia(x):
    w = x[x.dow == 2]
    nuevo = w[w.fecha < "2021-01-01"]; visto = w[w.fecha >= "2021-01-01"]
    pl = np.array([(rng.choice([-1, 1], len(w)) * w.mov.values).mean() for _ in range(2000)])
    otros = {"LMXJV"[k]: g.r_bruto.mean() for k, g in x.groupby("dow")}
    out = dict(ops=len(w), bruto=w.r_bruto.mean(), t_bruto=t(w.r_bruto), pb_bruto=w.pb.mean(), coste_r=w.coste_r.mean(),
               neto=w.neto.mean(), t_neto=t(w.neto), neto_x2=w.neto_x2.mean(), neto_hist=w.neto_hist.mean(),
               nuevo_ops=len(nuevo), nuevo_bruto=nuevo.r_bruto.mean(), nuevo_t_bruto=t(nuevo.r_bruto), nuevo_neto=nuevo.neto.mean(),
               visto_bruto=visto.r_bruto.mean(), visto_neto=visto.neto.mean(), placebo_p95=np.percentile(pl, 95), **{f"bruto_{k}": v for k, v in otros.items()})
    por_anio = w.groupby(w.fecha.dt.year).agg(bruto=("r_bruto", "mean"), neto=("neto", "mean"), pb=("pb", "mean"), n=("r_bruto", "size"))
    return out, por_anio

if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print("=" * 30, "GOTOBI (comprar 08:00→09:55 JST, stop 0,25 rango 14 d)")
    res = {}
    for sim in ["USDJPY", "EURJPY", "GBPJPY"]:
        x = gotobi(sim); o, pa = resumen_gotobi(sim, x); res[sim] = o
        x.to_csv(f"{AQUI}/gotobi_{sim}_ops.csv", index=False, float_format="%.6g")
        print(f"\n--- {sim}"); print(pd.Series(o).to_string()); print(pa.round(3).T.to_string())
    u = res["USDJPY"]
    crit = {"t neto ≥ 2,64": u["t_neto"] >= T_MIN, "nunca visto bruto t ≥ 2": u["nuevo_t_bruto"] >= 2,
            "nunca visto neto > 0": u["nuevo_neto"] > 0, "2018-26 neto > 0": u["visto_neto"] > 0,
            "costes ×2 > 0": u["neto_x2"] > 0, "bruto > p95 placebo": u["bruto"] > u["placebo_p95"],
            "réplica EURJPY/GBPJPY t ≥ 2 nunca visto": max(res["EURJPY"]["nuevo_t_bruto"], res["GBPJPY"]["nuevo_t_bruto"]) >= 2}
    print("\nCRITERIOS GOTOBI:", crit, "→", "PASA" if all(crit.values()) else "NO PASA")
    print("\n" + "=" * 30, "EIA (miércoles 10:35→14:30 NY a favor de 10:30-10:35, stop 0,5 ATR)")
    x = eia(); o, pa = resumen_eia(x); x.to_csv(f"{AQUI}/eia_ops.csv", index=False, float_format="%.6g")
    print(pd.Series(o).to_string()); print(pa.round(3).T.to_string())
    crit = {"t neto ≥ 2,64": o["t_neto"] >= T_MIN, "nunca visto bruto t ≥ 2": o["nuevo_t_bruto"] >= 2,
            "nunca visto neto > 0": o["nuevo_neto"] > 0, "2021-26 neto > 0": o["visto_neto"] > 0,
            "costes ×2 > 0": o["neto_x2"] > 0, "> p95 placebo dirección": o["bruto"] > o["placebo_p95"],
            "> otros 4 días": o["bruto"] > max(o[f"bruto_{k}"] for k in "LMJV")}
    print("\nCRITERIOS EIA:", crit, "→", "PASA" if all(crit.values()) else "NO PASA")
