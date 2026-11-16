"""Mejor descartado en Darwinex Zero (16-11-2026).
1) Gotobi USDJPY (comprar 08:00 -> 09:55 JST) con costes DZ CFD y 6J.
2) ORB GER40 con costes DZ (FDAX y CFD GDAXI).
3) Efecto en el DARWIN mezclado con el ORB US100 v018 (cuenta CFD).
Datos: metodo/revision/gotobi_USDJPY_ops.csv, metodo/v3/orb_ger40/, informes/donde_operar/serie_v018_be.csv
"""
import numpy as np, pandas as pd, glob
rng = np.random.default_rng(16112026)
B = '/home/user/yes-lab/'

def t(x): x = np.asarray(x); return x.mean()/x.std(ddof=1)*np.sqrt(len(x))

# ---------- 1. Gotobi
d = pd.read_csv(B+'metodo/revision/gotobi_USDJPY_ops.csv', parse_dates=['fecha'])
g, p = d[d.gotobi].copy(), d[~d.gotobi].copy()
# DZ CFD: comisión 0,005 % del nominal ida y vuelta (help.darwinex.com) = 0,0075 yenes a 150 = 0,75 pips;
# horquilla a las 23:00 UTC: FTMO medida 0,73-0,76; escenarios 0,4 / 0,55 / 0,8
esc = {'DZ CFD optimista (0,40 horq.)':1.15, 'DZ CFD central (0,55)':1.30, 'DZ CFD como FTMO (0,80)':1.55,
       'DZ futuros 6J':2.0, 'referencia: disparador 0,8':0.8}
print('=== GOTOBI USDJPY 2003-08 -> 2026 (', len(g), 'ops,', round(len(g)/23.2), '/año)')
print(f"bruto {g.r_bruto.mean():+.3f} R t {t(g.r_bruto):.2f} | {g.pips_bruto.mean():.2f} pips")
filas=[]
for k,c in esc.items():
    n = (g.pips_bruto-c)/g.dist_pips; n2=(g.pips_bruto-2*c)/g.dist_pips
    pl = (p.pips_bruto-c)/p.dist_pips
    a = n[g.fecha<'2018']; b = n[g.fecha>='2018']
    filas.append([k,c,n.mean(),t(n),a.mean(),b.mean(),t(b),n2.mean(),pl.mean(), n.sum()/23.2])
df = pd.DataFrame(filas,columns=['lugar','pips','neto_R','t','2003-17','2018-26','t_18-26','x2','placebo_neto','R_año'])
print(df.round(3).to_string(index=False))

# ---------- 2. ORB GER40
o = pd.concat([pd.read_csv(f,parse_dates=['fecha']) for f in sorted(glob.glob(B+'metodo/v3/orb_ger40/ger40_*.csv'))])
o = o.dropna(subset=['r']).copy()
print('\n=== ORB GER40 2013-26 (', len(o),'ops)')
for k,c in {'sin coste':0,'DZ FDAX (1 tick + 3 €x2 ≈ 0,0031 %)':0.000031,'DZ CFD GDAXI (≈ 0,0055 %)':0.000055,'FTMO 0,0052 %':0.000052}.items():
    n = o.r - c*o.px/o.dist
    print(f"{k:40s} neto {n.mean():+.3f} R t {t(n):.2f}  x2 {(o.r-2*c*o.px/o.dist).mean():+.3f}")

# ---------- 3. DARWIN: mezcla con ORB US100 (serie v018 BE)
s = pd.read_csv(B+'informes/donde_operar/serie_v018_be.csv', parse_dates=['d'])
orb = s.set_index('d').Rbe.groupby(pd.Grouper(freq='ME')).sum()
gc = g.assign(n=(g.pips_bruto-1.30)/g.dist_pips).set_index('fecha').n.groupby(pd.Grouper(freq='ME')).sum()
gm = o.assign(n=o.r-0.000031*o.px/o.dist).set_index('fecha').n.groupby(pd.Grouper(freq='ME')).sum()
m = pd.concat([orb,gc,gm],axis=1,keys=['orb','gotobi','ger40']).loc['2018-02':'2026-10'].fillna(0)
sh = lambda x: x.mean()/x.std()*np.sqrt(12)
print('\n=== DARWIN mensual 2018-02 -> 2026-10 (Sharpe anual de meses)')
print('corr mensual:\n', m.corr().round(2))
for c in m: print(f"{c:8s} Sharpe {sh(m[c]):.2f}")
z = m/m.std()
for combo in [['orb','gotobi'],['orb','ger40'],['orb','gotobi','ger40']]:
    print(f"{'+'.join(combo):18s} igual riesgo Sharpe {sh(z[combo].sum(1)):.2f}")
# peso óptimo del gotobi (máx Sharpe) para ver el techo
best=max(((w,sh(z.orb+w*z.gotobi)) for w in np.arange(0,1.01,0.05)),key=lambda x:x[1])
print(f"peso óptimo gotobi {best[0]:.2f} -> Sharpe {best[1]:.2f}")

# ---------- 4. Monte Carlo gotobi solo (bloques de 3 meses, 36 meses) coste central
gm_all = g.assign(n=(g.pips_bruto-1.30)/g.dist_pips).set_index('fecha').n.groupby(pd.Grouper(freq='ME')).sum()
v = gm_all.values; nb=12; res=[]
for _ in range(20000):
    st = rng.integers(0,len(v)-3,nb); x=np.concatenate([v[i:i+3] for i in st]); res.append(x.sum())
res=np.array(res)
print(f"\nMC 36 meses gotobi (coste 1,30): mediana {np.median(res):+.1f} R, p10 {np.percentile(res,10):+.1f}, P(<0) {np.mean(res<0):.0%}")
# ventanas 6 meses positivas
r6 = gm_all.rolling(6).sum().dropna(); print(f"ventanas 6 m positivas {np.mean(r6>0):.0%}  (ORB v018: {np.mean(orb.rolling(6).sum().dropna()>0):.0%})")
