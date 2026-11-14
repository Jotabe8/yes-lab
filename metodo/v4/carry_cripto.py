"""Candidato 2 v4: carry de financiación (largo contado / corto perpetuo) en Binance (ver PREREGISTRO_V4.md)."""
import glob, os, numpy as np, pandas as pd
D = "metodo/v4/datos/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
def velas(f):
    k = pd.read_csv(f)
    k = k[pd.to_numeric(k.open_time, errors="coerce").notna()]
    ot = k.open_time.astype("int64"); ot = np.where(ot > 1e14, ot // 1000, ot)
    return pd.Series(k.close.astype(float).to_numpy(), index=pd.to_datetime(ot, unit="ms").normalize()).groupby(level=0).last()
COSTE_LADO = 0.0010 + 0.0005    # contado + perpetuo, por entrada o salida
monedas = sorted({os.path.basename(f).split("_")[1] for f in glob.glob(D + "bn_*_funding.csv.gz")})
R, E, FUND = {}, {}, {}
for m in monedas:
    try:
        fr = pd.read_csv(D + f"bn_{m}_funding.csv.gz"); fr = fr[pd.to_numeric(fr.calc_time, errors="coerce").notna()]
        f = pd.Series(fr.last_funding_rate.astype(float).to_numpy(), index=pd.to_datetime(fr.calc_time.astype("int64"), unit="ms"))
        sp, pp = velas(D + f"bn_{m}_spot1d.csv.gz"), velas(D + f"bn_{m}_perp1d.csv.gz")
    except FileNotFoundError:
        continue
    fd = f.groupby(f.index.floor("D")).sum()          # financiación cobrada por el corto en el día UTC
    idx = sp.index.intersection(pp.index).intersection(fd.index)
    idx = idx[60:]                                    # 60 días cotizando
    if len(idx) < 200: continue
    r = (sp.pct_change() - pp.pct_change()).reindex(idx) + fd.reindex(idx)   # cierre UTC a cierre UTC; financiación del día
    FUND[m] = fd.reindex(idx)
    R[m] = r
R = pd.DataFrame(R).sort_index(); FUND = pd.DataFrame(FUND).reindex(R.index)
diario = FUND / 3                                     # aprox por 8 h (Binance cobra 3 veces al día casi siempre)
media7 = diario.rolling(7, min_periods=7).mean().shift(1)   # días t-7..t-1 conocidos al empezar el día t
# con 1 día de retraso del preregistro: señal de t-1 se aplica al día t+... -> shift adicional
media7 = media7.shift(1)
def regla(umbral_abrir=0.0001, cerrar=0.0):
    est = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    for c in R.columns:
        on = False; col = media7[c].to_numpy(); out = np.zeros(len(col))
        for i, v in enumerate(col):
            if np.isnan(v): on = False
            elif not on and v > umbral_abrir: on = True
            elif on and v < cerrar: on = False
            out[i] = on
        est[c] = out
    return est
def cartera(est, cols=None, mult=1.0):
    cols = cols or list(R.columns)
    e = est[cols]; r = R[cols]
    cambios = e.diff().abs().fillna(e)
    neto = e * r.fillna(0) - mult * cambios * COSTE_LADO
    n = e.sum(1)
    return (neto.sum(1) / n.replace(0, np.nan)).fillna(0), n
V1 = regla(); V2 = pd.DataFrame(1.0, index=R.index, columns=R.columns).where(R.notna(), 0.0)
grandes = [c for c in ("BTC", "ETH") if c in R.columns]; resto = [c for c in R.columns if c not in grandes]
def informe(nom, est, cols=None):
    r, n = cartera(est, cols); r2, _ = cartera(est, cols, 2.0)
    r = r[r.index >= "2020-03-01"]; r2 = r2[r2.index >= "2020-03-01"]
    mitad = r.index[len(r) // 2]
    vol = r.std() * np.sqrt(365); esc = 0.15 / vol if vol > 0 else 0
    eq = (r * esc).cumsum(); dd = (eq.cummax() - eq).max(); an = r.mean() * 365 * esc
    print(f"{nom:28s} días con posición {(n[r.index]>0).mean():.0%} | anual {r.mean()*365:+.1%} vol {vol:.1%} Sharpe {r.mean()/r.std()*np.sqrt(365):.2f} t {t(r):.2f}"
          f" | 1ª {r[:mitad].mean()*365:+.1%} 2ª {r[mitad:].mean()*365:+.1%} | ×2 {r2.mean()*365:+.1%} t {t(r2):.2f} | a vol 15 % DD {dd:.1%} DD/anual {dd/an if an>0 else np.inf:.1f}")
    return r
print("monedas:", list(R.columns), "desde", R.index[0].date())
r1 = informe("V1 principal (20 monedas)", V1)
informe("V2 siempre abierto", V2)
informe("V3 solo BTC+ETH", V1, grandes)
print("Réplicas obligatorias de V1:")
informe("  (a) BTC+ETH", V1, grandes); informe("  (b) resto", V1, resto)
print("por año V1 (%):", (r1.groupby(r1.index.year).sum() * 100).round(1).to_dict())
print("peor día V1", round(r1.min(), 4), r1.idxmin().date(), "| peor mes", round(r1.resample("ME").sum().min(), 4))
for a, b in (("2021-05-10", "2021-05-31"), ("2022-05-05", "2022-05-20"), ("2022-11-05", "2022-11-20"), ("2020-03-08", "2020-03-20")):
    print(f"  choque {a}→{b}: {r1[a:b].sum():+.2%}")
# placebo tiempo: rotar circularmente la exposición de cada moneda
rng = np.random.default_rng(0); pl = []
for _ in range(300):
    est = V1.copy()
    for c in est.columns: est[c] = np.roll(est[c].to_numpy(), rng.integers(len(est)))
    rp, _ = cartera(est); pl.append(rp[rp.index >= "2020-03-01"].mean())
print(f"placebo tiempo p95 {np.percentile(pl,95)*365:+.1%}/año vs V1 {r1.mean()*365:+.1%}")
r1.rename("r").to_frame().to_csv("metodo/v4/carry_v1_diaria.csv")
