# Reversión de varios días en índices (cuenta de futuros DZ). Ver PREREGISTRO.md: regla, costes y puertas fijados antes.
import sys, numpy as np, pandas as pd
from statistics import NormalDist
D = next((a for a in sys.argv[1:] if not a.startswith('--')), '../../datos_reversion_dz')
US = {'ES': ('GSPC', 0.66), 'NQ': ('NDX', 0.9), 'RTY': ('RUT', 0.36), 'YM': ('DJI', 2.2)}
EU = {'FDAX': ('GDAXI', 2.4), 'FESX': ('STOXX50E', 2.4)}
def t(r): r = np.asarray(r, float); return r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 1 else 0.0
def treq(n): return NormalDist().inv_cdf(1 - 0.05 / n)

def carga(n):
    d = pd.read_csv(f'{D}/{n}.csv', parse_dates=['Date']).set_index('Date').dropna()
    d = d[(d.High > d.Low) & (d.Close > 0)]
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    d['ATR'] = tr.rolling(20).mean(); return d.dropna()

def ops(d, coste, ibs=0.2, maxd=5, lado=1, entrada='cierre'):
    O, H, L, C, A = (d[c].values for c in ('Open', 'High', 'Low', 'Close', 'ATR')); idx = d.index
    IBS = (C - L) / (H - L); out = []; i = 1; n = len(C)
    while i < n - 1:
        sen = (IBS[i] < ibs and C[i] < C[i-1]) if lado == 1 else (IBS[i] > 1 - ibs and C[i] > C[i-1])
        if not sen: i += 1; continue
        e = i if entrada == 'cierre' else i + 1
        pe = C[i] if entrada == 'cierre' else O[i+1]
        j = i + 1
        while j < n - 1 and (j - i) < maxd and not ((C[j] > H[j-1]) if lado == 1 else (C[j] < L[j-1])): j += 1
        if entrada != 'cierre' and j < e: j = e
        r = lado * (C[j] - pe) / A[i]
        out.append((idx[i], idx[j], j - i, r, coste / A[i])); i = j + 1
    return pd.DataFrame(out, columns=['fecha', 'salida', 'dias', 'r_bruto', 'coste_r'])

def placebo(d, o, rng, reps=200):
    C, A = d.Close.values, d.ATR.values; n = len(C); dur = o.dias.values; res = []
    for _ in range(reps):
        e = rng.integers(1, n - 6, len(dur)); res.append(np.mean((C[e + dur] - C[e]) / A[e]))
    return np.array(res)

def corte(d, a, b): return d.loc[a:b]
rng = np.random.default_rng(17)
print('=== P1: 2003-2022, regla principal ===')
D1 = {k: corte(carga(n), '2003', '2022') for k, (n, c) in US.items()}
tot = []; plac = np.zeros(200); pos = 0
for k, (n, c) in US.items():
    o = ops(D1[k], c); p = placebo(D1[k], o, rng); tot.append(o)
    pos += o.r_bruto.mean() > 0; plac += p * len(o)
    print(f'{k}: n={len(o)} ({len(o)/20:.0f}/año) bruto {o.r_bruto.mean():+.3f} R t {t(o.r_bruto):.2f} | coste {o.coste_r.mean():.3f} R | '
          f'neto {(o.r_bruto-o.coste_r).mean():+.3f} | placebo media {p.mean():+.3f} p95 {np.percentile(p,95):+.3f} | días {o.dias.mean():.1f}')
a = pd.concat(tot); plac /= len(a)
print(f'AGREGADO US: n={len(a)} bruto {a.r_bruto.mean():+.3f} R t {t(a.r_bruto):.2f}, coste {a.coste_r.mean():.3f} R (×{a.r_bruto.mean()/a.coste_r.mean():.1f}), '
      f'placebo media {plac.mean():+.3f} p95 {np.percentile(plac,95):+.3f}, exceso {a.r_bruto.mean()-plac.mean():+.3f}, mercados >0: {pos}/4')
p1 = a.r_bruto.mean() >= 3 * a.coste_r.mean() and a.r_bruto.mean() > np.percentile(plac, 95) and pos >= 3
print('P1', 'PASA' if p1 else 'NO PASA')
if '--todo' not in sys.argv and not p1: sys.exit()

def agrega(dd, mk, **kw):
    return pd.concat([ops(dd[k], mk[k][1], **kw).assign(m=k) for k in mk])
print('\n=== P2: 2003-2022 ===')
net = lambda o, x=1: o.r_bruto - x * o.coste_r
print(f'neto {net(a).mean():+.3f} R t {t(net(a)):.2f} | neto coste×2 {net(a,2).mean():+.3f} R t {t(net(a,2)):.2f}')
an = net(a).groupby(a.fecha.dt.year).sum(); print(f'años positivos {(an>0).sum()}/{len(an)} ({(an>0).mean()*100:.0f} %)  ', ' '.join(f"{y}:{v:+.1f}" for y, v in an.items()))
ok_mes = True
for kw in ({'ibs': 0.15}, {'ibs': 0.25}, {'maxd': 4}, {'maxd': 6}):
    o = agrega(D1, US, **kw); ok_mes &= net(o).mean() > 0
    print(f'meseta {kw}: n={len(o)} neto {net(o).mean():+.3f} R t {t(net(o)):.2f}')
DE = {k: corte(carga(n), '2003', '2022') for k, (n, c) in EU.items()}
oe = agrega(DE, EU)
for k in EU: x = oe[oe.m == k]; print(f'réplica {k}: n={len(x)} bruto {x.r_bruto.mean():+.3f} neto {net(x).mean():+.3f} t {t(net(x)):.2f}')
print(f'réplica Europa: neto {net(oe).mean():+.3f} R t {t(net(oe)):.2f}')
oa = agrega(D1, US, entrada='apertura')
print(f'control entrada apertura siguiente: n={len(oa)} bruto {oa.r_bruto.mean():+.3f} R t {t(oa.r_bruto):.2f}')
oc = agrega(D1, US, lado=-1)
print(f'variante corta (informativa): n={len(oc)} bruto {oc.r_bruto.mean():+.3f} neto {net(oc).mean():+.3f} t {t(net(oc)):.2f}')
p2 = net(a, 2).mean() > 0 and (an > 0).mean() >= 0.6 and ok_mes and net(oe).mean() > 0 and oa.r_bruto.mean() > 0 and t(oa.r_bruto) >= 2
print('P2', 'PASA' if p2 else 'NO PASA')
if '--todo' not in sys.argv and not p2: sys.exit()

print('\n=== P3: fuera de muestra 2023-2026 (se abre una vez) ===')
D3 = {k: corte(carga(n), '2023', '2026') for k, (n, c) in US.items()}
o3 = agrega(D3, US)
for k in US: x = o3[o3.m == k]; print(f'{k}: n={len(x)} neto {net(x).mean():+.3f} t {t(net(x)):.2f}')
p3c = agrega({k: corte(carga(n), '2023', '2026') for k, (n, c) in US.items()}, US)
pl3 = np.mean([placebo(D3[k], o3[o3.m == k], rng).mean() for k in US])
print(f'OOS US: n={len(o3)} bruto {o3.r_bruto.mean():+.3f} neto {net(o3).mean():+.3f} R t {t(net(o3)):.2f} (placebo exposición ≈ {pl3:+.3f})')
DT = {k: carga(n).loc['2003':] for k, (n, c) in US.items()}; ot = agrega(DT, US)
print(f'TOTAL 2003-26: n={len(ot)} neto {net(ot).mean():+.3f} R t {t(net(ot)):.2f} vs requerido {treq(10):.2f}')
p3 = net(o3).mean() > 0 and t(net(o3)) >= 1 and t(net(ot)) >= treq(10)
print('P3', 'PASA' if p3 else 'NO PASA')
