"""v18: prueba preregistrada (PREREGISTRO.md). Régimen de caída S; R1 corto 10:00→16:00; R2 sigue 9:30-10:00."""
import sys, numpy as np, pandas as pd
from statistics import NormalDist
R = '../../orb_acciones'; MK = ['US500', 'US100', 'US30']
COSTE_PB, SLIP_PB, STOP_ATR = 1.0, 0.5, 0.30
rng = np.random.default_rng(18)

def carga(m):
    b = pd.concat([pd.read_csv(f'{R}/indices_2012/{m}_b30.csv'), pd.read_csv(f'{R}/indices/{m}_b30.csv')])
    nov = pd.read_csv(f'datos/{m}_b30_nov.csv'); b = pd.concat([b, nov[nov.fecha > b.fecha.max()]])
    b = b.drop_duplicates(['fecha', 'bar'], keep='last')
    k = b.groupby('fecha').bar.count(); b = b[b.fecha.isin(k[k == 13].index)]
    b['fecha'] = pd.to_datetime(b.fecha); return b.sort_values(['fecha', 'bar'])

B = {m: carga(m) for m in MK}
def diario(b):
    g = b.groupby('fecha'); d = pd.DataFrame({'o': g.o.first(), 'h': g.h.max(), 'l': g.l.min(), 'c': g.c.last(), 'spr': g.spr.mean()})
    tr = pd.concat([d.h - d.l, (d.h - d.c.shift()).abs(), (d.l - d.c.shift()).abs()], axis=1).max(axis=1)
    d['atr'] = tr.rolling(20).mean().shift(); return d
DD = {m: diario(B[m]) for m in MK}
def regimen(umbral):
    c = DD['US500'].c; return (c <= (1 - umbral) * c.rolling(60).max()).shift(1).fillna(False).astype(bool)

def simula(m, dias, lado_fn, con_stop=True):
    b = B[m]; d = DD[m]; out = []
    for f, x in b[b.fecha.isin(dias)].groupby('fecha'):
        a = d.atr.get(f, np.nan)
        if not np.isfinite(a): continue
        O, H, L, C = x.o.values, x.h.values, x.l.values, x.c.values
        lado = lado_fn(f, O, C)
        if lado == 0: continue
        pe = C[0]; st = STOP_ATR * a; ps = pe - lado * st; salida = C[12]; parado = False
        if con_stop:
            for i in range(1, 13):
                if (lado == 1 and L[i] <= ps) or (lado == -1 and H[i] >= ps):
                    salida = ps; parado = True; break
        r = lado * (salida - pe) / st
        coste = (COSTE_PB + (SLIP_PB if parado else 0)) * 1e-4 * pe / st
        out.append((f, m, lado, r, coste, parado, d.spr.get(f) / st))
    return pd.DataFrame(out, columns=['fecha', 'm', 'lado', 'r_bruto', 'coste_r', 'stop', 'spr_duka_r'])

R1 = lambda f, O, C: -1
R2 = lambda f, O, C: int(np.sign(C[0] - O[0]))
def t_sem(x, f):
    x = np.asarray(x, float); mu = x.mean(); s = pd.Series(x - mu).groupby(pd.to_datetime(f).dt.to_period('W').values).sum()
    return mu * len(x) / np.sqrt((s ** 2).sum()) if len(x) > 2 else 0.0
def t(x): x = np.asarray(x, float); return x.mean() / x.std(ddof=1) * np.sqrt(len(x))
def net(o, k=1): return o.r_bruto - k * o.coste_r
def resumen(o, eti):
    n = net(o); años = o.fecha.dt.year.nunique()
    print(f"{eti}: n={len(o)} ({len(o)/max(años,1)/len(MK):.0f}/año/mercado) bruto {o.r_bruto.mean():+.3f} R | coste {o.coste_r.mean():.3f} "
          f"(×{o.r_bruto.mean()/o.coste_r.mean():+.1f}) | neto {n.mean():+.3f} t_sem {t_sem(n, o.fecha):.2f} (t op {t(n):.2f}) | ×2 {net(o,2).mean():+.3f} | stops {o.stop.mean()*100:.0f} %")
    return n.mean(), t_sem(n, o.fecha)

def todos(dias, fn, cs=True): return pd.concat([simula(m, dias, fn, cs) for m in MK])
S = regimen(0.05); fechas = DD['US500'].index
A0, A1 = '2011-01-01', '2022-12-31'
Sfit = fechas[(S.reindex(fechas).values) & (fechas >= A0) & (fechas <= A1)]
NS = fechas[(~S.reindex(fechas).values) & (fechas >= A0) & (fechas <= A1)]
print(f"Días S 2011-22: {len(Sfit)} de {((fechas>=A0)&(fechas<=A1)).sum()} ({len(Sfit)/12:.0f}/año)")
res = {}
for nom, fn in (('R1', R1), ('R2', R2)):
    print(f'\n=== {nom} — P1/T0 ajuste 2011-2022 ===')
    for cs in (True, False):
        o = todos(Sfit, fn, cs); mu, ts = resumen(o, f"{nom} {'con stop' if cs else 'sin stop'}")
        if cs: res[nom] = o
    o = res[nom]
    for m in MK: resumen(o[o.m == m], f"   {m}")
    print(f"   horquilla Dukascopy medida ≈ {o.spr_duka_r.mean()*2:.3f} R ida y vuelta (FTMO usada {o.coste_r.mean():.3f})")
    # placebo
    pl = []
    for _ in range(200):
        if nom == 'R1':
            dd = pd.DatetimeIndex(rng.choice(NS, len(Sfit), replace=False)); pl.append(todos(dd, R1).r_bruto.mean())
        else:
            lados = {f: rng.choice([-1, 1]) for f in Sfit}; pl.append(todos(Sfit, lambda f, O, C: lados[f]).r_bruto.mean())
    pl = np.array(pl); print(f"   placebo ({'mismo corto en días fuera de S' if nom=='R1' else 'lado aleatorio mismos días'}): media {pl.mean():+.3f} p95 {np.percentile(pl,95):+.3f}"
                             f" | real {o.r_bruto.mean():+.3f} → {'SUPERA' if o.r_bruto.mean() > np.percentile(pl,95) else 'NO supera'}")
    n = net(o); pos = sum(net(o[o.m == m]).mean() > 0 for m in MK)
    p1 = o.r_bruto.mean() >= 3 * o.coste_r.mean() and n.mean() > 0 and t_sem(n, o.fecha) >= 2.4 and pos == 3 and o.r_bruto.mean() > np.percentile(pl, 95)
    print(f"   P1 {nom}: {'PASA' if p1 else 'NO PASA'}")
    an = n.groupby(o.fecha.dt.year).sum(); print('   años:', ' '.join(f"{y}:{v:+.1f}" for y, v in an.items()), f"| positivos {(an>0).mean()*100:.0f} %")
    for u in (0.04, 0.06):
        Su = regimen(u); d2 = fechas[(Su.reindex(fechas).values) & (fechas >= A0) & (fechas <= A1)]
        resumen(todos(d2, fn), f"   régimen vecino {u:.0%}")
    res[nom + '_p1'] = p1

print('\n=== Control: R1 en todos los días 2011-22 (deriva de sesión sin condición) ===')
todo = fechas[(fechas >= A0) & (fechas <= A1)]
resumen(todos(todo, R1), 'corto todos los días')

if '--oos' in sys.argv:
    print('\n=== P3: 2023-2026 (se abre una vez) ===')
    So = fechas[(S.reindex(fechas).values) & (fechas >= '2023-01-01')]
    print(f"Días S 2023-26: {len(So)}")
    for nom, fn in (('R1', R1), ('R2', R2)):
        o = todos(So, fn); resumen(o, f"{nom} OOS")
        St = fechas[(S.reindex(fechas).values) & (fechas >= A0)]; ot = todos(St, fn)
        print(f"   total 2011-26 t_sem {t_sem(net(ot), ot.fecha):.2f} vs requerido {NormalDist().inv_cdf(1-0.05/4):.2f}")
        ot.to_csv(f'salidas_ops_{nom}.csv', index=False)
    # semana actual
    sem = fechas[fechas >= '2026-11-16']; print('Semana 16-20 nov (¿S?):', [f"{f:%d}:{bool(S.get(f))}" for f in sem])
