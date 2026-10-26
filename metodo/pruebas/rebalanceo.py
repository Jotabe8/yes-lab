"""P1-P4 del embudo para el rebalanceo 60/40 de fin de mes (ver PREREGISTRO.md).
Uso: python rebalanceo.py DIR_D1 IEF_JSON   (desde la raíz de yes-lab para importar metodo)"""
import json, sys
import numpy as np, pandas as pd
from metodo.embudo import embudo, t_stat

DIR, IEF = sys.argv[1], sys.argv[2]
MK = {"US500": "USA500IDXUSD", "US100": "USATECHIDXUSD", "US30": "USA30IDXUSD", "US2000": "USSC2000IDXUSD",
      "GER40": "DEUIDXEUR", "UK100": "GBRIDXGBP", "EU50": "EUSIDXEUR"}
COSTE, HOLD = 0.05, 5

def d1(f):
    d = pd.read_csv(f"{DIR}/{f}.csv", parse_dates=["date"])
    d = d[(d.vol > 1) & (d.date.dt.weekday < 5)].set_index("date").sort_index()
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(20).mean()
    return d

ief = pd.DataFrame(json.load(open(IEF))); ief = ief.assign(d=pd.to_datetime(ief.d)).set_index("d").c
spx = d1(MK["US500"]).close

def señales():
    """Por mes: fecha de entrada (6.ª sesión antes del fin), fecha de salida y señal acciones - bonos."""
    out = []
    s = spx[spx.index >= "2016-11-01"]
    for _, m in s.groupby(s.index.to_period("M")):
        if len(m) < 10: continue
        ent, sal = m.index[-HOLD - 1], m.index[-1]
        prev = spx[spx.index < m.index[0]]
        if len(prev) == 0: continue
        r_acc = m.loc[ent] / prev.iloc[-1] - 1
        b = ief[ief.index <= ent]; b0 = ief[ief.index < m.index[0]]
        if len(b) == 0 or len(b0) == 0: continue
        out.append((ent, sal, r_acc - (b.iloc[-1] / b0.iloc[-1] - 1)))
    return pd.DataFrame(out, columns=["ent", "sal", "sig"])

S = señales()

def ops(nombre, umbral=0.0, signo=None):
    d = d1(MK[nombre]); rows = []
    for ent, sal, sig in S.itertuples(index=False):
        if abs(sig) <= umbral: continue
        # entrada al cierre del día de señal (o el anterior disponible en este mercado)
        e = d[d.index <= ent]
        if len(e) == 0 or np.isnan(e.atr.iloc[-1]): continue
        x = d[(d.index > e.index[-1]) & (d.index <= sal)]
        if len(x) == 0: continue
        dirn = -np.sign(sig) if signo is None else signo
        stop = 1.5 * e.atr.iloc[-1]; p0 = e.close.iloc[-1]; r = None
        for _, b in x.iterrows():
            if (dirn > 0 and b.low <= p0 - stop) or (dirn < 0 and b.high >= p0 + stop): r = -1.0; break
        if r is None: r = dirn * (x.close.iloc[-1] - p0) / stop
        rows.append((sal, r, COSTE, dirn))
    return pd.DataFrame(rows, columns=["fecha", "r_bruto", "coste_r", "dir"])

print(f"meses con señal: {len(S)} ({S.ent.min().date()} → {S.sal.max().date()}), señal>0 (corto) {(S.sig>0).mean():.0%}")
print("\nP1 bruto por mercado (ajuste 2016-22 | prueba 2023-25), R/op y t")
res = {}
for u in (0.0, 0.02):
    for m in MK:
        o = ops(m, u); res[(m, u)] = o
        a, p = o[o.fecha < "2023-01-01"], o[o.fecha >= "2023-01-01"]
        print(f"  {m:<7} |señal|>{u:.0%}: n {len(o):>3}  total {o.r_bruto.mean():+.3f} t {t_stat(o.r_bruto):+.2f}"
              f" | ajuste {a.r_bruto.mean():+.3f} t {t_stat(a.r_bruto):+.2f} | prueba {p.r_bruto.mean():+.3f} t {t_stat(p.r_bruto):+.2f}")

# Placebo: dirección aleatoria en los mismos días (US500, todas las señales)
rng = np.random.default_rng(0); base = ops("US500")
largo = ops("US500", signo=+1).set_index("fecha").r_bruto
med = [np.mean(largo.values * rng.choice([-1, 1], len(largo))) for _ in range(500)]
print(f"\nPlacebo US500 (500 réplicas dirección aleatoria): p95 {np.percentile(med, 95):+.3f}  vs estrategia {base.r_bruto.mean():+.3f}")
print(f"Solo largo en esos días (deriva): {largo.mean():+.3f} R/op")

print("\nEmbudo US500 (todas las señales, 14 pruebas):")
print(embudo(base, n_pruebas=14, corte_oos="2023-01-01", placebo=lambda s: largo.values * np.random.default_rng(s).choice([-1, 1], len(largo))))
