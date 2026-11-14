"""Prueba preregistrada v7 (PREREGISTRO_NOCHE_FX.md): reversión nocturna M15 en cruces FX.
uso: python noche_fx.py carpeta_datos serie_v018.csv"""
import sys, glob, os, numpy as np, pandas as pd

DECIDE = ["gbpusd", "eurcad", "eurusd", "chfjpy", "audcad", "euraud", "eurchf", "usdcad", "usdchf"]
REPLICA = ["audnzd", "nzdcad", "gbpchf", "eurnzd"]
COM = 5e-5  # 5 $/lote i/v ≈ 0,005 % del nominal

def cargar(f):
    d = pd.read_parquet(f)
    esc = 1e3 if "jpy" in os.path.basename(f) else 1e5
    for c in d.columns[1:]:
        d[c] = d[c] / esc
    t = pd.to_datetime(d.t, unit="ms", utc=True).dt.tz_convert("America/New_York")
    d["min"] = t.dt.hour * 60 + t.dt.minute          # minuto de APERTURA de la barra
    d["ts"] = t
    d["mc"] = (d.close_b + d.close_a) / 2
    mh, ml = (d.high_b + d.high_a) / 2, (d.low_b + d.low_a) / 2
    d["sma"] = d.mc.rolling(20).mean()
    d["sd"] = d.mc.rolling(20).std(ddof=0)
    pc = d.mc.shift()
    tr = np.maximum(mh - ml, np.maximum(abs(mh - pc), abs(ml - pc)))
    d["atr"] = tr.rolling(14).mean()
    # sesión: desde las 17:00 NY
    d["ses"] = (t - pd.Timedelta(hours=17)).dt.date
    return d.reset_index(drop=True)

def operar(d, ini, fin, salida_min, k=2.0):
    """ini/fin: minuto NY del CIERRE de la barra señal; salida_min: minuto NY de apertura de la barra de salida por tiempo."""
    mn = d["min"].values; cierre = (mn + 15) % 1440
    ob, hb, lb = d.open_b.values, d.high_b.values, d.low_b.values
    oa, ha, la = d.open_a.values, d.high_a.values, d.low_a.values
    mc, sma, sd, atr = d.mc.values, d.sma.values, d.sd.values, d.atr.values
    ses = d.ses.values; ts = d.ts.values
    if ini <= fin:
        enw = (cierre >= ini) & (cierre <= fin)
    else:
        enw = (cierre >= ini) | (cierre <= fin)
    sig = np.where(mc > sma + k * sd, -1, np.where(mc < sma - k * sd, 1, 0)) * enw
    out, usado, n = [], set(), len(d)
    i = 20
    idx = np.nonzero(sig)[0]
    for i in idx:
        if ses[i] in usado or i + 1 >= n or np.isnan(atr[i]):
            continue
        j = i + 1
        if (ts[j] - ts[i]) > np.timedelta64(16, "m"):
            continue
        s = sig[i]; usado.add(ses[i]); R = 3 * atr[i]
        if R <= 0:
            continue
        ent = oa[j] if s > 0 else ob[j]
        entm = (oa[j] + ob[j]) / 2
        stop, stopm = ent - s * R, entm - s * R
        sal = salm = None; k_ = j
        hasta = ts[j] + np.timedelta64(10, "h")
        stopped = False
        while k_ < n:
            if mn[k_] == salida_min or ts[k_] > hasta or (k_ > j and (ts[k_] - ts[k_ - 1]) > np.timedelta64(16, "m")):
                sal = ob[k_] if s > 0 else oa[k_]; salm = (ob[k_] + oa[k_]) / 2; break
            # stop, lado real
            if s > 0:
                if ob[k_] <= stop: sal = ob[k_]; stopped = True
                elif lb[k_] <= stop: sal = stop; stopped = True
            else:
                if oa[k_] >= stop: sal = oa[k_]; stopped = True
                elif ha[k_] >= stop: sal = stop; stopped = True
            if stopped:
                om = (ob[k_] + oa[k_]) / 2; lm = (lb[k_] + la[k_]) / 2; hm = (hb[k_] + ha[k_]) / 2
                salm = stopm if not ((s > 0 and om <= stopm) or (s < 0 and om >= stopm)) else om
                break
            if (s > 0 and mc[k_] >= sma[k_]) or (s < 0 and mc[k_] <= sma[k_]):
                if k_ + 1 < n:
                    k_ += 1
                    sal = ob[k_] if s > 0 else oa[k_]; salm = (ob[k_] + oa[k_]) / 2
                break
            k_ += 1
        if sal is None:
            continue
        neto = (s * (sal - ent) - COM * ent) / R
        bruto = s * (salm - entm) / R
        out.append((pd.Timestamp(ts[min(k_, n - 1)]).date(),
                    pd.Timestamp(ts[i]).year, s, bruto, neto, entm, salm, R, stopped))
    return pd.DataFrame(out, columns=["fecha", "anio", "lado", "bruto", "neto", "entm", "salm", "R", "stop"])

def tstat(x):
    x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan

def resumen(nombre, ops):
    if len(ops) == 0:
        return f"{nombre}: sin ops"
    c = ops.bruto - ops.neto
    n2 = ops.bruto - 2 * c
    a, b = ops[ops.anio <= 2017], ops[ops.anio >= 2018]; r = ops[ops.anio >= 2023]
    anios = ops.anio.nunique()
    return (f"{nombre}: n {len(ops)} ({len(ops)/anios:.0f}/año) bruto {ops.bruto.mean():+.3f} t {tstat(ops.bruto):.2f} | "
            f"neto {ops.neto.mean():+.3f} t {tstat(ops.neto):.2f} | coste {c.mean():.3f} R | ×2 {n2.mean():+.3f} | "
            f"2010-17 {a.neto.mean():+.3f} t {tstat(a.neto):.2f} | 2018-26 {b.neto.mean():+.3f} t {tstat(b.neto):.2f} | "
            f"2023-26 {r.neto.mean():+.3f} | gana {np.mean(ops.neto>0)*100:.0f} % | stops {ops.stop.mean()*100:.0f} %")

def main():
    carpeta, v018 = sys.argv[1], sys.argv[2]
    datos = {os.path.basename(f)[:-8]: cargar(f) for f in sorted(glob.glob(f"{carpeta}/*.parquet"))}
    print("pares:", list(datos))
    conf = {"V1 base": (18*60+30, 23*60, 2*60, 2.0), "V2 2,5σ": (18*60+30, 23*60, 2*60, 2.5),
            "V3 hasta 01:00": (18*60+30, 60, 2*60, 2.0), "PLACEBO hora 08-12": (8*60, 12*60, 16*60, 2.0)}
    res = {}
    for nom, (a, b, s, k) in conf.items():
        res[nom] = {p: operar(d, a, b, s, k) for p, d in datos.items()}
    for nom in conf:
        print(f"\n=== {nom} ===")
        for p in DECIDE + REPLICA:
            if p in res[nom]:
                print("  ", resumen(p.upper(), res[nom][p]))
        dec = pd.concat([res[nom][p] for p in DECIDE if p in res[nom]])
        print(" CARTERA DECISIÓN", resumen("", dec))
        if nom == "V1 base":
            rep = pd.concat([res[nom][p] for p in REPLICA if p in res[nom]])
            print(" RÉPLICA", resumen("", rep))
            # por año
            print(" por año (neto medio, n):", dec.groupby("anio").neto.agg(["mean", "count"]).round(3).to_dict("index"))
            # placebo dirección: mismas entradas/salidas, lado aleatorio (en precio medio, sin stop)
            mov = (dec.salm - dec.entm) / dec.R
            real = (dec.lado * mov).mean()
            rng = np.random.default_rng(7)
            pl = [(rng.choice([-1, 1], len(mov)) * mov).mean() for _ in range(200)]
            print(f" placebo dirección: real {real:+.3f} vs p95 {np.percentile(pl,95):+.3f}")
            # DD y correlación
            diario = dec.groupby("fecha").neto.sum()
            eq = diario.cumsum(); dd = (eq.cummax() - eq).max()
            anual = dec.neto.sum() / dec.anio.nunique()
            print(f" DD máx {dd:.1f} R vs 3× anual {3*anual:.1f} R")
            s = pd.read_csv(v018, parse_dates=["d"]).set_index("d").R
            s.index = s.index.date
            u = pd.concat([diario, s], axis=1).fillna(0)
            u = u[(pd.to_datetime(u.index) >= "2018-01-23")]
            print(f" corr diaria con v018: {u.corr().iloc[0,1]:+.3f}")
            dec.to_csv(os.path.join(os.path.dirname(__file__), "ops_v1_decision.csv"), index=False)

if __name__ == "__main__":
    main()
