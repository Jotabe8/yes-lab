"""v19b: por qué el paseo aleatorio da +0,09 R y cuánto vale el momento de entrada sobre la beta.
Uso: python -m metodo.v19.diagnostico"""
import numpy as np, pandas as pd
from metodo.embudo import ftmo_2step, t_agrupado, t_stat
from metodo.sinteticos import velas_paseo
from metodo.v19.tendencia_cripto import backtest, cargar, CORTE, LUGARES


def semanal(velas_dict, look=28, log=False):
    """Matriz semana × moneda de: señal (0/1), N·ret (R si comprado)."""
    S, X = {}, {}
    for nom, v in velas_dict.items():
        c = v["close"].reindex(pd.date_range(v.index[0], v.index[-1], freq="D")).ffill()
        lr = np.log(c).diff()
        vol = lr.rolling(30, min_periods=25).std() * np.sqrt(7)
        dom = c.index[c.index.dayofweek == 6]
        dom = dom[(dom >= c.index[0] + pd.Timedelta(days=60)) & (dom + pd.Timedelta(days=7) <= c.index[-1])]
        r = (np.log(c.shift(-7) / c) if log else c.shift(-7) / c - 1).loc[dom]
        S[nom] = (c / c.shift(look) - 1 > 0).astype(float).loc[dom]
        X[nom] = (r / vol.loc[dom]).replace([np.inf, -np.inf], np.nan)
    return pd.DataFrame(S), pd.DataFrame(X)


def exceso(S, X, nombre):
    """Exceso del momento de entrada: Σ (s − p_moneda)·X por semana (p = fracción de semanas compradas)."""
    ok = X.notna() & S.notna()
    p = S.where(ok).mean()
    e = ((S - p) * X).where(ok).sum(axis=1)
    e.index = e.index + pd.Timedelta(days=7)
    d = e.index < pd.Timestamp(CORTE)
    t = lambda s: s.mean() / s.std() * np.sqrt(len(s))
    print(f"{nombre:44s} exceso {e.mean():+.3f} R/semana t {t(e):5.2f} | ajuste t {t(e[d]):5.2f} | OOS {e[~d].mean():+.3f} t {t(e[~d]):5.2f}")
    return e


V = cargar("bn_*_spot1d.csv.gz")
R = cargar("*_spot1d.csv.gz", excluir_bn=True)

print("1) Paseo aleatorio: estrategia vs siempre comprado en las MISMAS velas sintéticas (20 réplicas)")
dif, est, sie = [], [], []
for s in range(20):
    Vp = {k: velas_paseo(v, semilla=s * 100 + i, por_minuto=False) for i, (k, v) in enumerate(V.items())}
    Sp, Xp = semanal(Vp)
    ok = Xp.notna() & Sp.notna()
    est.append((Sp * Xp).where(ok).stack().loc[lambda z: z != 0].mean())
    sie.append(Xp.where(ok).stack().mean())
    e = ((Sp - Sp.where(ok).mean()) * Xp).where(ok).sum(axis=1)
    dif.append(e.mean() / e.std() * np.sqrt(len(e)))
    Sl, Xl = semanal(Vp, log=True)
    if s == 0:
        print(f"   réplica 0 con rendimiento log: estrategia {(Sl * Xl).stack().loc[lambda z: z != 0].mean():+.3f}, "
              f"siempre {Xl.stack().mean():+.3f}")
print(f"   R estrategia {np.mean(est):+.3f}, siempre comprado {np.mean(sie):+.3f} (sesgo de Jensen: E[e^x − 1] > 0 con media log 0)")
print(f"   t del exceso de momento en el paseo: media {np.mean(dif):+.2f}, rango {np.min(dif):+.2f} a {np.max(dif):+.2f}, |t|≥2 en {np.mean(np.abs(dif) >= 2):.0%}")

print("\n2) Exceso de momento sobre la beta en datos reales (neutral a la exposición)")
S, X = semanal(V); e_p = exceso(S, X, "principal 20 monedas, aritmético")
Sl, Xl = semanal(V, log=True); exceso(Sl, Xl, "principal 20 monedas, log")
for look in (22, 34):
    a, b = semanal(V, look=look); exceso(a, b, f"lookback {look}")
Sr, Xr = semanal(R); e_r = exceso(Sr, Xr, "réplica 126 monedas")
mx = ["BTC", "ETH"]; exceso(S[mx], X[mx], "solo BTC+ETH")
print("   exceso por año (principal, R/semana):", e_p.groupby(e_p.index.year).mean().round(3).to_dict())
print("   exceso por año (réplica):", e_r.groupby(e_r.index.year).mean().round(3).to_dict())

print("\n3) Estrategia en log (sin el regalo de Jensen), neto exchange")
ok = X.notna() & S.notna()
n_log = (Sl * Xl).where(ok).stack().loc[lambda z: z != 0]
print(f"   R/op log {n_log.mean():+.3f} (aritmético {(S * X).where(ok).stack().loc[lambda z: z != 0].mean():+.3f})")

print("\n4) FTMO 2-Step con riesgo por moneda reducido (las posiciones van juntas: hasta 20 a la vez)")
for lugar in ("ftmo",):
    c, sw = LUGARES[lugar]
    o = backtest(V, coste=c, swap=sw)
    n = o.r_bruto - o.coste_r
    dia = n.groupby(o.fecha.dt.date).sum().to_numpy()
    ctl = (n - n.mean()).groupby(o.fecha.dt.date).sum().to_numpy()
    sim = o.groupby("fecha").size()
    print(f"   posiciones abiertas por semana: media {sim.mean():.1f}, máx {sim.max()}")
    for r in (0.001, 0.002, 0.003, 0.005):
        ev = ftmo_2step(dia, riesgo=r); evc = ftmo_2step(ctl, riesgo=r)
        print(f"   riesgo {r*100:.1f} %/moneda: EV/cuota {ev['ev_cuota']:+.0f} € (p pasar {ev['p_pasar']:.0%}) vs control {evc['ev_cuota']:+.0f} €")
print("\n   Ojo: el EV diario aquí usa las R semanales en la fecha de cierre; el DD diario real intrasemana es mayor.")


def diario(velas_dict, look=28, coste=0.0005, swap=0.25, siempre=False):
    """R diaria a precio de mercado (todos los días naturales): N·Δc/c_entrada; costes el lunes de cambio."""
    tot = None
    for nom, v in velas_dict.items():
        c = v["close"].reindex(pd.date_range(v.index[0], v.index[-1], freq="D")).ffill()
        lr = np.log(c).diff()
        vol = lr.rolling(30, min_periods=25).std() * np.sqrt(7)
        es_dom = (c.index.dayofweek == 6) & (c.index >= c.index[0] + pd.Timedelta(days=60))
        s = (c / c.shift(look) - 1 > 0).astype(float) if not siempre else pd.Series(1.0, c.index)
        N = (s / vol).where(es_dom).replace([np.inf, -np.inf], np.nan)
        N = N.where(es_dom).ffill().fillna(0.0)               # decidido el domingo al cierre, vale 7 días
        ent = c.where(es_dom).ffill()
        pnl = N.shift(1) * (c - c.shift(1)) / ent.shift(1)
        cst = (N - N.shift(1)).abs() * coste + N.abs() * swap / 365
        r = (pnl - cst).fillna(0.0)
        tot = r if tot is None else tot.add(r, fill_value=0.0)
    return tot


print("\n5) P4 bien hecho: R diaria a mercado (365 días/año), FTMO 0,05 %/lado + swap 25 %/año")
Vd = {k: v for k, v in V.items()}
d_est = diario(Vd)["2019-03":]
d_bet = diario(Vd, siempre=True)["2019-03":]
for nm, d in (("estrategia", d_est), ("siempre comprado", d_bet)):
    print(f"   {nm}: R/año {d.mean()*365:+.1f}, peor día {d.min():+.1f} R, Sharpe {d.mean()/d.std()*np.sqrt(365):.2f}, "
          f"2023+ Sharpe {d['2023':].mean()/d['2023':].std()*np.sqrt(365):.2f}")
for r in (0.001, 0.002, 0.003, 0.005):
    ev = ftmo_2step(d_est.to_numpy(), riesgo=r); evb = ftmo_2step(d_bet.to_numpy(), riesgo=r)
    evc = ftmo_2step((d_est - d_est.mean()).to_numpy(), riesgo=r)
    ev3 = ftmo_2step(d_est["2023":].to_numpy(), riesgo=r)
    print(f"   riesgo {r*100:.1f} %/moneda: EV/cuota estrategia {ev['ev_cuota']:+.0f} € (pasa {ev['p_pasar']:.0%}) | solo 2023+ "
          f"{ev3['ev_cuota']:+.0f} € | siempre comprado {evb['ev_cuota']:+.0f} € | control media 0 {evc['ev_cuota']:+.0f} €")

print("\n6) P4 sin deriva de cripto: se quita a la estrategia la beta de su exposición media (supuesto: cripto con deriva 0)")
expo = 0.48   # fracción media de semanas compradas (salida principal)
quitar = expo * d_bet.mean()
d0 = d_est - quitar
print(f"   R/año estrategia {d_est.mean()*365:+.1f} − beta {quitar*365:+.1f} = {d0.mean()*365:+.1f}; Sharpe {d0.mean()/d0.std()*np.sqrt(365):.2f}; "
      f"2023+ {d0['2023':].mean()/d0['2023':].std()*np.sqrt(365):.2f}")
for r in (0.001, 0.002, 0.003):
    ev = ftmo_2step(d0.to_numpy(), riesgo=r); evc = ftmo_2step((d0 - d0.mean()).to_numpy(), riesgo=r)
    print(f"   riesgo {r*100:.1f} %: EV/cuota {ev['ev_cuota']:+.0f} € (pasa {ev['p_pasar']:.0%}) vs control media 0 {evc['ev_cuota']:+.0f} €")
print("   por año R (estrategia sin deriva):", (d0.groupby(d0.index.year).sum()).round(1).to_dict())
