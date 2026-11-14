"""Candidato 1 v4: prima de volatilidad, corto en VX de vencimiento constante 30 días (ver PREREGISTRO_V4.md)."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
def t(x): x = pd.Series(x).dropna(); return x.mean() / x.std() * np.sqrt(len(x))

def indice(n):
    d = pd.read_csv(D + f"{n}_History.csv"); d.columns = [c.upper() for c in d.columns]
    d["DATE"] = pd.to_datetime(d.DATE); return d.set_index("DATE").CLOSE

vx = pd.read_csv(D + "VX_futuros.csv.gz", parse_dates=["Trade Date", "expiry"])
vx = vx[vx.Settle > 0].rename(columns={"Trade Date": "f"})
vx = vx[vx.f < vx.expiry]                       # el día del vencimiento la liquidación es el VRO
piv = vx.pivot_table(index="f", columns="expiry", values="Settle")
dias = piv.index
filas = []
for i in range(1, len(dias)):
    d0, d1 = dias[i - 1], dias[i]
    exps = sorted(e for e in piv.columns if e > d0 and np.isfinite(piv.at[d0, e]) and np.isfinite(piv.at[d1, e]))
    if len(exps) < 2: continue
    e1, e2 = exps[0], exps[1]
    # pesos tipo VXX: días hábiles al 1er vencimiento / días entre vencimientos, objetivo 30 días naturales
    T1, T2 = (e1 - d0).days, (e2 - d0).days
    w1 = np.clip((T2 - 30) / (T2 - T1), 0, 1); w2 = 1 - w1
    F0 = w1 * piv.at[d0, e1] + w2 * piv.at[d0, e2]
    dF = w1 * (piv.at[d1, e1] - piv.at[d0, e1]) + w2 * (piv.at[d1, e2] - piv.at[d0, e2])
    filas.append(dict(f=d1, r_corto=-dF / F0, F0=F0, F1=piv.at[d0, e1]))
s = pd.DataFrame(filas).set_index("f")
vix, v3 = indice("VIX"), indice("VIX3M")
ratio = (vix / v3).reindex(s.index).ffill()
sen = ratio.shift(1)                              # señal del cierre t-1 → se opera t-1 → t ... con 1 día más de retraso:
sen = sen.shift(1)                                # cierre t-2 decide la exposición del día t (preregistro: 1 día de retraso)
vixl = vix.reindex(s.index).ffill().shift(2)
# coste: entrar o salir = 1 tick (0,05) + 2×2 $ comisión /1000 $ por punto → en puntos 0,05+0,004; traspaso diario ~1/21 × 2 patas × 0,025
tick = 0.054
def correr(expo, mult=1.0):
    expo = expo.astype(float).fillna(0)
    cambio = expo.diff().abs().fillna(expo.iloc[0])
    coste = mult * (cambio * tick / s.F0 + expo * (2 * 0.025 / 21) / s.F0)
    return expo * s.r_corto - coste
V = {"V1 contango": (sen < 1), "V2 siempre": pd.Series(True, s.index), "V3 contango y VIX<30": (sen < 1) & (vixl < 30)}
res = {}
for k, e in V.items():
    r = correr(e); r2 = correr(e, 2)
    res[k] = r
    vol = r.std() * np.sqrt(252); esc = 0.15 / vol
    eq = (r * esc).cumsum(); dd = (eq.cummax() - eq).max()
    mitad = r.index[len(r) // 2]
    print(f"{k:22s} expuesto {e.mean():.0%} | R/año {r.mean()*252:+.1%} vol {vol:.1%} Sharpe {r.mean()/r.std()*np.sqrt(252):.2f} t {t(r):.2f}"
          f" | 1ª {r[:mitad].mean()*252:+.1%} 2ª {r[mitad:].mean()*252:+.1%} | ×2 {r2.mean()*252:+.1%} t {t(r2):.2f}"
          f" | a vol 15 %: anual {r.mean()*252*esc:+.1%} DD {dd:.1%} DD/anual {dd/(r.mean()*252*esc):.1f}")
r1 = res["V1 contango"]
print("peor día V1", r1.min().round(3), r1.idxmin().date(), "| peor mes", r1.resample("ME").sum().min().round(3), r1.resample("ME").sum().idxmin().date())
for a, b in (("2018-01-25", "2018-02-28"), ("2020-02-15", "2020-04-15"), ("2024-07-25", "2024-08-15"), ("2022-01-01", "2022-12-31")):
    print(f"  choque {a}→{b}: V1 {r1[a:b].sum():+.1%}  V2 {res['V2 siempre'][a:b].sum():+.1%}")
print("por año V1:", (r1.groupby(r1.index.year).sum() * 100).round(1).to_dict())
# placebo: misma fracción expuesta, tiempo aleatorio por bloques de 20 días
rng = np.random.default_rng(0); e1 = V["V1 contango"].astype(float).to_numpy(); n = len(e1); pl = []
for _ in range(1000):
    k = rng.integers(n); ep = np.roll(e1, k)
    pl.append(correr(pd.Series(ep, s.index)).mean())
print(f"placebo tiempo (rotación circular de la exposición) p95 {np.percentile(pl, 95)*252:+.1%}/año vs V1 {r1.mean()*252:+.1%}")
r1.rename("r").to_frame().to_csv("metodo/v4/vrp_v1_diaria.csv")
