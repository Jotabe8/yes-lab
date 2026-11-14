# Prueba preregistrada: rebalanceo por umbral 60/40 (Harvey-Mazzoleni-Melone). Ver PREREGISTRO_REBALANCEO_UMBRAL.md
import numpy as np, pandas as pd, sys
D = sys.argv[1] if len(sys.argv) > 1 else 'metodo/v4/datos'
ORB = '/mnt/project-files/donde-operar/serie_v018_be.csv'
def rd(f):
    x = pd.read_csv(f'{D}/{f}', parse_dates=['Date']).set_index('Date'); return x[~x.index.duplicated()]
g = rd('ene_GSPC.csv'); z = rd('ZN_F.csv'); spy = rd('SPY.csv')
df = pd.DataFrame({'acc': g.Close, 'bon': z.Close}).dropna()
df = df[df.index >= '2000-09-21']
re = df.acc.pct_change().fillna(0).values; rb = df.bon.pct_change().fillna(0).values
deltas = np.arange(0, 0.02501, 0.001)
S = np.zeros(len(df))
for dl in deltas:
    w = 0.6
    for t in range(len(df)):
        if t > 0:
            a = w*(1+re[t]); b = (1-w)*(1+rb[t]); w = a/(a+b)
        d = w - 0.6
        if abs(d) > dl + 1e-12:
            S[t] += d; w = 0.6
S /= len(deltas)
df['S'] = S
fin_paper = '2023-03-17'
sd = df.S[df.index <= fin_paper].std()
df['z'] = df.S / sd
df['r1'] = df.acc.pct_change().shift(-1)          # cierre t -> cierre t+1
df['rb1'] = df.bon.pct_change().shift(-1)
df['r0'] = df.acc.pct_change(); df['rb0'] = df.bon.pct_change()
o = spy.Open; c = spy.Close
df['oc1'] = (c/o - 1).reindex(df.index).shift(-1)  # apertura t+1 -> cierre t+1
df = df.dropna(subset=['r1', 'r0', 'rb0', 'rb1'])

def hac_t(y, X, L=5):
    X = np.column_stack([np.ones(len(y)), X]); b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X@b
    XtXi = np.linalg.inv(X.T@X); u = X*e[:, None]; Sm = u.T@u
    for l in range(1, L+1):
        G = u[l:].T@u[:-l]; Sm += (1-l/(L+1))*(G+G.T)
    V = XtXi@Sm@XtXi; return b, b/np.sqrt(np.diag(V))

print('Días', len(df), df.index[0].date(), df.index[-1].date(), ' sd(S) paper', round(sd, 5))
print('Frecuencia z!=0: %.1f %%' % (100*(df.z != 0).mean()))
for nom, m in [('paper 2000-23', df.index <= fin_paper), ('no visto 2023-26', df.index > fin_paper), ('todo', df.index == df.index)]:
    x = df[m]
    b, t = hac_t(x.r1.values*1e4, x.z.values)
    b2, t2 = hac_t(x.r1.values*1e4, np.column_stack([x.z, x.r0*1e4, (x.r0-x.rb0)*1e4]))
    b3, t3 = hac_t((x.r1-x.rb1).values*1e4, x.z.values)
    print(f'{nom}: r_acc(t+1) = {b[1]:+.2f} pb por z (t {t[1]:+.2f}) | con controles {b2[1]:+.2f} (t {t2[1]:+.2f}) | acc-bonos {b3[1]:+.2f} (t {t3[1]:+.2f})')

def estrategia(df, umbral, tipo, cm=1.0):
    pos = np.where(df.z >= umbral, -1, np.where(df.z <= -umbral, 1, 0))
    if tipo == 'cc':
        r = pos*df.r1.values*1e4
        prev = np.r_[0, pos[:-1]]
        # entrada/salida 0,6 pb cada una (cambio de 2 = salida + entrada); noche 3 pb
        cost = cm*(0.6*np.abs(pos-prev) + 3.0*(pos != 0))
    else:
        r = pos*df.oc1.values*1e4; cost = cm*0.6*(pos != 0)
    s = pd.DataFrame({'pos': pos, 'bruto': r, 'neto': r-cost}, index=df.index)
    s = s[s.pos != 0].dropna()
    return s

def resumen(s, nombre):
    def st(x):
        return f'{x.mean():+6.2f} pb t {x.mean()/x.std()*np.sqrt(len(x)):+5.2f} n {len(x)}' if len(x) > 2 else 'n<3'
    anos = (s.index[-1]-s.index[0]).days/365.25
    mitad = s.index[0] + (s.index[-1]-s.index[0])/2
    print(f'\n== {nombre}: {len(s)/anos:.0f} ops/año')
    print('  bruto', st(s.bruto), '| neto', st(s.neto))
    print('  1ª mitad neto', st(s.neto[s.index < mitad]), '| 2ª mitad', st(s.neto[s.index >= mitad]))
    print('  paper neto', st(s.neto[s.index <= fin_paper]), '| no visto', st(s.neto[s.index > fin_paper]))
    sin = s[~((s.index.year == 2008) | ((s.index.year == 2020) & (s.index.month <= 6)))]
    print('  sin 2008 ni 1S-2020 neto', st(sin.neto))
    print('  largos', st(s.neto[s.pos > 0]), '| cortos', st(s.neto[s.pos < 0]))
    print('  por año neto (pb/op):', ' '.join(f"{y}:{v:+.0f}" for y, v in s.neto.groupby(s.index.year).mean().items()))
    return s

s1 = resumen(estrategia(df, 1.0, 'cc'), 'V1 |z|>=1 cierre-cierre')
s1x2 = estrategia(df, 1.0, 'cc', 2.0); print('  costes x2 neto %+.2f pb t %+.2f' % (s1x2.neto.mean(), s1x2.neto.mean()/s1x2.neto.std()*np.sqrt(len(s1x2))))
s2 = resumen(estrategia(df[df.index >= '2010-01-04'], 1.0, 'oc'), 'V2 |z|>=1 apertura-cierre (SPY)')
s3 = resumen(estrategia(df, 0.5, 'cc'), 'V3 |z|>=0,5 cierre-cierre')

# placebo: desplazamientos circulares de z
rng = np.random.default_rng(1); pl = []
zz = df.z.values
for k in range(500):
    sh = rng.integers(20, len(df)-20); d2 = df.copy(); d2['z'] = np.roll(zz, sh)
    pl.append(estrategia(d2, 1.0, 'cc').neto.sum())
print('\nPlacebo V1 (suma neta pb): real %.0f, p95 placebo %.0f, p50 %.0f' % (s1.neto.sum(), np.percentile(pl, 95), np.percentile(pl, 50)))

# correlación con ORB
orb = pd.read_csv(ORB, parse_dates=['d']).set_index('d').R
dia = pd.Series(0.0, index=df.index); dia[s1.index] = s1.neto
j = pd.concat([dia, orb], axis=1).fillna(0); j = j[j.index >= orb.index[0]]
print('Corr diaria V1 vs ORB v018: %.3f' % j.corr().iloc[0, 1])
# DD a vol 15 %
x = dia[dia.index >= '2000-09-21']/1e4
vol = x.std()*np.sqrt(252); esc = 0.15/vol; eq = (x*esc).cumsum()
print('A vol 15 %%: anual %.1f %%, DD máx %.1f %%' % (x.mean()*252*esc*100, (eq.cummax()-eq).max()*100))
