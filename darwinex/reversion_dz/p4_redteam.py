# P4 (DZ) y comprobaciones del red team para la reversión de varios días. Ejecutar después de reversion.py.
import sys, numpy as np, pandas as pd
sys.argv = [sys.argv[0], '--todo']
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import reversion as R
US, net, t = R.US, R.net, R.t
DT = {k: R.carga(n).loc['2003':] for k, (n, c) in US.items()}
ot = R.agrega(DT, US)

print('=== Red team 1: dependencia entre mercados (t por fecha de señal) ===')
g = ot.assign(n=net(ot)).groupby('fecha').n.mean()
print(f'fechas únicas {len(g)}; neto medio por fecha {g.mean():+.3f} R t {t(g):.2f}')
for a, b in (('2003', '2022'), ('2023', '2026')):
    x = g.loc[a:b]; print(f'  {a}-{b}: n={len(x)} t {t(x):.2f}')

print('\n=== Red team 2: futuros (instrumento real). Señal del contado, entrada en la apertura Globex siguiente (después de la señal) ===')
D = '../../datos_reversion_dz'
FUT = {'ES': ('GSPC', 'ES'), 'NQ': ('NDX', 'NQ'), 'YM': ('DJI', 'YM'), 'RTY': ('RUT', 'RTY')}
res = []
for k, (c, f) in FUT.items():
    try: fu = pd.read_csv(f'futuros/{f}.csv', parse_dates=['Date']).set_index('Date').dropna()
    except FileNotFoundError: continue
    cs = DT[k]; j = cs.join(fu, rsuffix='_f', how='inner')
    # salto de roll: diferencia de rendimientos futuro vs contado > 4 sd
    dif = j.Close_f.pct_change() - j.Close.pct_change(); roll = (dif - dif.mean()).abs() > 4 * dif.std()
    o = R.ops(cs, US[k][1]); pos = {d: i for i, d in enumerate(j.index)}
    for _, r in o.iterrows():
        if r.fecha not in pos or r.salida not in pos: continue
        i, s = pos[r.fecha], pos[r.salida]
        if i + 1 > s or roll.iloc[i+1:s+1].any(): continue
        res.append((k, r.fecha, (j.Close_f.iloc[s] - j.Open_f.iloc[i+1]) / r.ATR if 'ATR' in r else (j.Close_f.iloc[s] - j.Open_f.iloc[i+1]) / cs.ATR.loc[r.fecha], r.coste_r))
f = pd.DataFrame(res, columns=['m', 'fecha', 'r', 'c']); f['n'] = f.r - f.c
for k in f.m.unique(): x = f[f.m == k]; print(f'{k}: n={len(x)} neto {x.n.mean():+.3f} R t {t(x.n):.2f}')
gf = f.groupby('fecha').n.mean(); print(f'futuros US por fecha: n={len(gf)} neto {gf.mean():+.3f} R t {t(gf):.2f}; 2023-26 {gf.loc["2023":].mean():+.3f} t {t(gf.loc["2023":]):.2f}')

print('\n=== Red team 3: colas (sin stop) ===')
x = net(ot); print(f'peor op {x.min():+.2f} R, p1 {np.percentile(x,1):+.2f} R; 5 peores: ' + ', '.join(f"{d.date()} {m} {v:+.1f}" for d, m, v in ot.assign(x=x).nsmallest(5, 'x')[['fecha', 'm', 'x']].values))

print('\n=== P4: Sharpe frente a comprar y mantener, y DARWIN con el ORB ===')
def diaria(cs, o):
    r = cs.Close.pct_change(); pos = pd.Series(0.0, index=cs.index)
    for _, q in o.iterrows(): pos.loc[(cs.index > q.fecha) & (cs.index <= q.salida)] = 1.0
    cost = pd.Series(0.0, index=cs.index); cost.loc[o.fecha] = (o.coste_r.values * cs.ATR.loc[o.fecha].values / cs.Close.loc[o.fecha].values)
    return (pos * r - cost).fillna(0), r.fillna(0), pos
sr = lambda s: s.mean() / s.std() * np.sqrt(252)
port = []
for k in US:
    cs = DT[k]; o = ot[ot.m == k]; s, bh, pos = diaria(cs, o)
    print(f'{k}: exposición {pos.mean()*100:.0f} % días | Sharpe estrategia {sr(s):.2f} vs comprar y mantener {sr(bh):.2f} | 2023-26 {sr(s.loc["2023":]):.2f} vs {sr(bh.loc["2023":]):.2f}')
    port.append(s / s.std())
P = pd.concat(port, axis=1).mean(axis=1); print(f'cesta 4 US (igual vol): Sharpe {sr(P):.2f}; peor DD {(P.cumsum().cummax()-P.cumsum()).max()/P.std()/np.sqrt(252):.2f} años de vol')
orb = pd.read_csv('serie_v018_be.csv', parse_dates=['d']).set_index('d'); om = (orb.Rbe - 0.05).resample('ME').sum()
pm = P.resample('ME').sum().loc[om.index.min():om.index.max()]; om = om.loc[pm.index.min():]
j = pd.concat([om, pm], axis=1, keys=['orb', 'rev']).dropna(); j['rev'] *= j.orb.std() / j.rev.std()
mix = (j.orb + j.rev); mix *= j.orb.std() / mix.std()
srm = lambda s: s.mean() / s.std() * np.sqrt(12); dd = lambda s: (s.cumsum().cummax() - s.cumsum()).max()
print(f'2018-26 mensual: corr {j.orb.corr(j.rev):+.2f} | Sharpe ORB {srm(j.orb):.2f}, reversión {srm(j.rev):.2f}, mezcla 50/50 {srm(mix):.2f} | peor DD (R) ORB {dd(j.orb):.1f}, mezcla {dd(mix):.1f}')
mh = j.orb + j.rev * 0.5 / 1; mh = j.orb + (j.rev - j.rev.mean() / 2); mh *= j.orb.std() / mh.std()
print(f'con la media de la reversión a la mitad: Sharpe mezcla {srm(mh):.2f}')
j.assign(mezcla=mix).to_csv('mensual_orb_reversion.csv')
