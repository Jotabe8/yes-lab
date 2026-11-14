"""Candidato 7 v4 (PREREGISTRO_V4_R5.md): corto del perpetuo recién listado frente a BTC."""
import glob, os, re, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
D = "metodo/v4/datos/"; L = D + "lis/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
def velas(f):
    k = pd.read_csv(f); k = k[pd.to_numeric(k.open_time, errors="coerce").notna()]
    ot = k.open_time.astype("int64"); ot = np.where(ot > 1e14, ot // 1000, ot)
    return pd.Series(k.close.astype(float).to_numpy(), pd.to_datetime(ot, unit="ms").normalize()).groupby(level=0).last()
def fund(f):
    if not os.path.exists(f): return pd.Series(dtype=float)
    fr = pd.read_csv(f); fr = fr[pd.to_numeric(fr.calc_time, errors="coerce").notna()]
    s = pd.Series(fr.last_funding_rate.astype(float).to_numpy(), pd.to_datetime(fr.calc_time.astype("int64"), unit="ms"))
    return s.groupby(s.index.floor("D")).sum()
ESTABLES = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "USDE", "USD1", "BFUSD", "XUSD", "RLUSD", "USDT"}
btc_p, btc_f = velas(L + "BTCUSDT_k.csv.gz"), fund(L + "BTCUSDT_f.csv.gz")
lst = pd.read_csv(L + "listados.csv")
eventos = {}
for s in lst.sym:
    b = s[:-4]
    if b in ESTABLES or b == "BTC" or re.match(r"^1000+", b) or re.match(r"^1M", b): continue
    if not os.path.exists(L + f"{s}_k.csv.gz"): continue
    p = velas(L + f"{s}_k.csv.gz")
    if len(p) < 5 or p.index[0] < pd.Timestamp("2020-01-01") or p.index[0] > pd.Timestamp("2026-09-30"): continue
    eventos[b] = (p, fund(L + f"{s}_f.csv.gz"))
print("eventos:", len(eventos))
def operacion(p, f, d0, N, c_nuevo=0.001, c_btc=0.0005):
    """Serie diaria de la operación corto nuevo / largo BTC desde el cierre de d0, N días."""
    dias = pd.date_range(d0 + pd.Timedelta(days=1), periods=N)
    pn = p.reindex(dias); last = pn.last_valid_index()
    if last is None: return None
    pn = pn.loc[:last]
    rn = pn.pct_change(); rn.iloc[0] = pn.iloc[0] / p[d0] - 1
    pb = btc_p.reindex(pd.DatetimeIndex([d0]).append(pn.index)).ffill(); rb = pb.pct_change().iloc[1:]
    r = 0.5 * (-rn.fillna(0) + rb.values) + 0.5 * (f.reindex(pn.index).fillna(0) - btc_f.reindex(pn.index).fillna(0))
    r.iloc[0] -= 0.5 * (c_nuevo + c_btc); r.iloc[-1] -= 0.5 * (c_nuevo + c_btc)
    return r
def cartera(N, mult=1.0, fuente=None, rng=None):
    series = []
    for b, (p, f) in eventos.items():
        d0 = p.index[0] + pd.Timedelta(days=2)
        if fuente is not None:
            ok = [c for c, (pp, ff) in fuente.items() if pp.first_valid_index() is not None and pp.first_valid_index() < d0 - pd.Timedelta(days=365) and d0 in pp.index]
            if not ok: continue
            pp, ff = fuente[ok[rng.integers(len(ok))]]; r = operacion(pp, ff, d0, N, 0.0005 * mult, 0.0005 * mult)
        else:
            if d0 not in p.index: continue
            r = operacion(p, f, d0, N, 0.001 * mult, 0.0005 * mult)
        if r is not None: series.append(r.rename(b))
    M = pd.concat(series, axis=1)
    return M.mean(axis=1), M
r1, M1 = cartera(30)
tot = M1.sum()                             # resultado de cada evento (sobre el capital de la operación)
mitad = r1.index[len(r1) // 2]
print(f"V1 30 días: días {len(r1)}, media diaria {r1.mean():+.4%} t {t(r1):.2f} | 1ª {r1[:mitad].mean():+.4%} 2ª {r1[mitad:].mean():+.4%}")
print(f"   por evento: media {tot.mean():+.2%} mediana {tot.median():+.2%} % ganadores {(tot>0).mean():.0%} peor {tot.min():+.1%} ({tot.idxmin()}) mejor {tot.max():+.1%}")
print("   por año (media por evento %):", (tot.groupby(M1.apply(lambda c: c.first_valid_index()).dt.year).mean() * 100).round(1).to_dict())
r2, _ = cartera(30, mult=2); print(f"V1 costes ×2: media diaria {r2.mean():+.4%} t {t(r2):.2f}")
for N in (14, 60):
    r, M = cartera(N); print(f"V{2 if N==14 else 3} {N} días: t {t(r):.2f}, media por evento {M.sum().mean():+.2%}")
# placebo: monedas listadas hace > 1 año (universos ya descargados)
pool = {}
for f in glob.glob(D + "*_perp1d.csv.gz"):
    bn = os.path.basename(f); b = bn.split("_")[1] if bn.startswith("bn_") else bn.split("_")[0]
    ffile = D + (f"bn_{b}_funding.csv.gz" if bn.startswith("bn_") else f"{b}_funding.csv.gz")
    pool[b] = (velas(f), fund(ffile))
rng = np.random.default_rng(3); pl = []
for i in range(200):
    rp, _ = cartera(30, fuente=pool, rng=rng); pl.append(rp.mean())
print(f"placebo (moneda antigua al azar, mismas fechas): p95 media diaria {np.percentile(pl,95):+.4%} (media {np.mean(pl):+.4%}) vs V1 {r1.mean():+.4%}")
r1.rename("r").to_frame().to_csv("metodo/v4/listados_v1_diaria.csv")
