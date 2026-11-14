"""Oro largo en horas de Asia con coste Darwinex Zero (preregistro: PREREGISTRO_ORO_ASIA.md).
Uso: python darwinex/oro_asia.py datos_oro"""
import sys, glob, gzip, numpy as np, pandas as pd

D = sys.argv[1] if len(sys.argv) > 1 else "datos_oro"

def serie(ins):
    p = {}
    for lado in ("bid", "ask"):
        f = sorted(glob.glob(f"{D}/{ins}-h1-{lado}-*.csv.gz"))[0]
        x = pd.read_csv(f)
        x.index = pd.to_datetime(x["timestamp"], unit="ms", utc=True)
        p[lado] = x
    o = (p["bid"]["open"] + p["ask"]["open"]) / 2
    o = o.dropna()
    o.index = o.index.tz_convert("America/New_York")
    return o[o > 0]

def precio(o, ts):
    """precio de apertura de la barra que empieza a la hora ts (o la siguiente hasta 30 min después)."""
    i = o.index.searchsorted(ts)
    if i >= len(o) or o.index[i] - ts > pd.Timedelta("30min"):
        return np.nan
    return o.iloc[i]

def ventanas(o, h0, largo):
    """rentabilidad de h0 a h0+largo (hora NY) cada día de sesión."""
    dias = pd.date_range(o.index[0].normalize(), o.index[-1].normalize(), freq="D", tz="America/New_York")
    out = {}
    idx = o.index
    for d in dias:
        a = d + pd.Timedelta(hours=h0); b = a + pd.Timedelta(hours=largo)
        pa, pb = precio(o, a), precio(o, b)
        if np.isfinite(pa) and np.isfinite(pb):
            out[d] = np.log(pb / pa)
    return pd.Series(out)

def t(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)), len(x)

def bp(x): return f"{x*1e4:+.2f} pb"

def informe(ins, o):
    print(f"\n===== {ins.upper()}  {o.index[0].date()} → {o.index[-1].date()}  ({len(o)} barras H1) =====")
    # noche: 19:00 del día d (dom-jue) a 03:00 del día d+1
    noche = ventanas(o, 19, 8)
    noche = noche[noche.index.dayofweek.isin([6, 0, 1, 2, 3])]
    noche.index = noche.index + pd.Timedelta(days=1)          # fecha = día que acaba (lun-vie)
    resto = ventanas(o, 3, 15)                                 # 03:00 → 18:00 del mismo día
    df = pd.concat({"n": noche, "r": resto}, axis=1).dropna()
    df["D"] = df.n - 8 / 15 * df.r
    tt, n = t(df.D)
    print(f"PRINCIPAL  D = noche − 8/15·resto: media {bp(df.D.mean())}  t {tt:.2f}  n {n}")
    for nom, s in (("2012-18", df.loc[:"2018"]), ("2019-26", df.loc["2019":])):
        a, m = t(s.D); print(f"   {nom}: D {bp(s.D.mean())} t {a:.2f} n {m} | noche {bp(s.n.mean())} | resto {bp(s.r.mean())}")
    for nom, c in (("GC 1 pb", 1e-4), ("GC ×2", 2e-4), ("CFD 2 pb", 2e-4), ("CFD ×2", 4e-4)):
        a, m = t(df.n - c); print(f"   noche neta {nom}: {bp((df.n - c).mean())} t {a:.2f}")
    a, _ = t(df.n); print(f"   noche bruta {bp(df.n.mean())} t {a:.2f} | resto 15 h {bp(df.r.mean())} | día completo {bp((df.n+df.r).mean())}")
    print("   año a año (D, noche, resto, pb):")
    for y, s in df.groupby(df.index.year):
        print(f"     {y}: D {s.D.mean()*1e4:+6.2f}  noche {s.n.mean()*1e4:+6.2f}  resto {s.r.mean()*1e4:+6.2f}  n {len(s)}")
    # placebo: ventanas de 8 h con cada hora de inicio
    print("   placebo de hora (media 8 h por hora de inicio NY, pb, t):")
    filas = []
    for h in range(24):
        s = ventanas(o, h, 8)
        s = s[s.index.dayofweek.isin([6, 0, 1, 2, 3, 4])]
        a, m = t(s); filas.append((h, s.mean() * 1e4, a, m))
    pl = pd.DataFrame(filas, columns=["h", "pb", "t", "n"]).set_index("h")
    print(pl.round(2).to_string())
    r19 = (pl.pb > pl.pb.loc[19]).sum()
    print(f"   la ventana 19:00 queda {r19 + 1}ª de 24 (1ª = mejor)")
    return df

res = {}
for ins in ("xauusd", "xagusd"):
    try:
        res[ins] = informe(ins, serie(ins))
    except IndexError:
        print("sin datos", ins)
