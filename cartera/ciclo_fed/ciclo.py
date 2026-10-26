# Ciclo de la Fed: comprado en semanas pares (ver PREREGISTRO.md). Stop recorrido día a día.
import numpy as np, pandas as pd, sys
from embudo import embudo, t_stat
FOMC = """2011-01-26 2011-03-15 2011-04-27 2011-06-22 2011-08-09 2011-09-21 2011-11-02 2011-12-13
2012-01-25 2012-03-13 2012-04-25 2012-06-20 2012-08-01 2012-09-13 2012-10-24 2012-12-12
2013-01-30 2013-03-20 2013-05-01 2013-06-19 2013-07-31 2013-09-18 2013-10-30 2013-12-18
2014-01-29 2014-03-19 2014-04-30 2014-06-18 2014-07-30 2014-09-17 2014-10-29 2014-12-17
2015-01-28 2015-03-18 2015-04-29 2015-06-17 2015-07-29 2015-09-17 2015-10-28 2015-12-16
2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-03-03 2020-03-15 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10""".split()
FOMC = pd.to_datetime(FOMC)
MKT = {"US500": ("USA500IDXUSD", 1.0e-4), "US30": ("USA30IDXUSD", 0.5e-4), "US100": ("USATECHIDXUSD", 0.8e-4),
       "US2000": ("USSC2000IDXUSD", 1.5e-4), "GER40": ("DEUIDXEUR", 0.9e-4), "FRA40": ("FRAIDXEUR", 1.3e-4),
       "EU50": ("EUSIDXEUR", 3.0e-4), "UK100": ("GBRIDXGBP", 1.9e-4), "JP225": ("JPNIDXJPY", 2.6e-4),
       "HK50": ("HKGIDXHKD", 5.0e-4), "AUS200": ("AUSIDXAUD", 2.0e-4)}
FIN = 0.0002  # financiación por noche natural

def cargar(f):
    d = pd.read_csv(f"../../data/D1/{f}.csv", parse_dates=["date"]).set_index("date").sort_index()
    d = d[(d.index.weekday < 5) & (d.index >= "2010-10-01")]
    d = d[d.vol > d.vol.rolling(50, min_periods=5).median() * 0.2]   # quita velas fantasma
    tr = np.maximum(d.high - d.low, np.maximum((d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()))
    d["atr"] = tr.rolling(20).mean().shift(0)
    return d

def semanas(idx, desplaz=0):
    # sesiones desde el FOMC más reciente (el día −1 cuenta como semana 0 del siguiente)
    pos = np.full(len(idx), np.nan)
    f_idx = idx.searchsorted(FOMC)          # posición del día del FOMC (o el siguiente hábil)
    for j, p in enumerate(f_idx):
        fin = f_idx[j + 1] - 1 if j + 1 < len(f_idx) else len(idx)
        for i in range(max(p - 1, 0), min(fin, len(idx))):
            pos[i] = i - p
    pos = pos + desplaz
    return np.floor((pos + 1) / 5)

def operaciones(d, spr, par=True, desplaz=0):
    k = semanas(d.index, desplaz)
    dentro = (k % 2 == 0) if par else (k % 2 == 1)
    dentro = pd.Series(dentro & ~np.isnan(k), index=d.index)
    filas, i, n = [], 1, len(d)
    c, o_, lo, atr = d.close.values, d.open.values, d.low.values, d.atr.values
    while i < n:
        if dentro.iloc[i] and not dentro.iloc[i - 1] and np.isfinite(atr[i - 1]):
            e = c[i - 1]; st = 2 * atr[i - 1]; stop = e - st; j = i; rb = None
            while j < n and dentro.iloc[j]:
                if o_[j] <= stop: rb = (o_[j] - e) / st; break
                if lo[j] <= stop: rb = -1.0; break
                j += 1
            jf = min(j, n - 1) if rb is not None else j - 1
            if rb is None: rb = (c[jf] - e) / st
            noches = (d.index[jf] - d.index[i - 1]).days
            filas.append((d.index[jf], rb, (spr * e + FIN * e * noches) / st))
            i = jf + 1
        else:
            i += 1
    return pd.DataFrame(filas, columns=["fecha", "r_bruto", "coste_r"])

datos = {m: cargar(f) for m, (f, _) in MKT.items()}
todo, impar = [], []
for m, (f, spr) in MKT.items():
    o = operaciones(datos[m], spr).assign(mercado=m); todo.append(o)
    oi = operaciones(datos[m], spr, par=False); impar.append(oi)
    a = o.fecha < "2019"
    print(f"{m:7s} {len(o):4d} ops | bruto {o.r_bruto.mean():+.3f} t {t_stat(o.r_bruto):.2f} | ajuste {o[a].r_bruto.mean():+.3f} | OOS {o[~a].r_bruto.mean():+.3f}"
          f" | coste {o.coste_r.mean():.3f} | impares {oi.r_bruto.mean():+.3f}")
J = pd.concat(todo).sort_values("fecha").reset_index(drop=True)
I = pd.concat(impar)
print(f"\nTODOS: {len(J)} ops, bruto {J.r_bruto.mean():+.3f} t {t_stat(J.r_bruto):.2f} | semanas impares {I.r_bruto.mean():+.3f} t {t_stat(I.r_bruto):.2f}")
J.to_csv("ops_ciclo.csv", index=False)

rng = np.random.default_rng(0)
cache = {}
def plac(s):
    off = int(np.random.default_rng(s).integers(1, 10)) * (1 if s % 2 else -1)
    if off not in cache:
        cache[off] = pd.concat([operaciones(datos[m], spr, desplaz=off) for m, (f, spr) in MKT.items()]).r_bruto.to_numpy()
    return cache[off]
print(embudo(J[["fecha", "r_bruto", "coste_r"]], n_pruebas=11, corte_oos="2019-01-01", placebo=plac, n_placebo=40))
print("placebos distintos usados:", sorted(cache), {k: round(v.mean(), 3) for k, v in cache.items()})
