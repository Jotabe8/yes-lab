# (1) Variante en la cuenta CFD de DZ (con swap) para ES/NQ; (2) Monte Carlo 36 meses de dz_sim (mismo que informes previos).
import sys, io, contextlib, os, numpy as np, pandas as pd
sys.argv = [sys.argv[0], '--todo']
with contextlib.redirect_stdout(io.StringIO()):
    import reversion as R
t = R.t
print('=== Cuenta CFD de DZ: horquilla 0,9 pt + 2×2,75 $ (10 $/pt) y swap largo 6,5 %/año por noche natural ===')
for k in ('NQ', 'ES'):
    cs = R.carga(R.US[k][0]).loc['2003':]; o = R.ops(cs, 1.45)
    noches = (o.salida - o.fecha).dt.days.values
    swap = noches * 0.065 / 365 * cs.Close.loc[o.fecha].values / cs.ATR.loc[o.fecha].values
    n = o.r_bruto - o.coste_r - swap
    print(f'{k}: coste fijo {o.coste_r.mean():.3f} R + swap {swap.mean():.3f} R → neto {n.mean():+.3f} R t {t(n):.2f}; 2023-26 {n[o.fecha.dt.year>=2023].mean():+.3f}')
print('\n=== Monte Carlo 36 meses (dz_sim, 1 R ≈ 0,45 % del DARWIN) ===')
src = open('dz_sim_base.py').read().split('filas=[]')[0].replace('../dos-orb/serie_v018_be.csv', 'serie_v018_be.csv')
b = {}; exec(src, b)
j = pd.read_csv('mensual_orb_reversion.csv', index_col=0)
mh = j.orb + (j.rev - j.rev.mean() / 2); mh *= j.orb.std() / mh.std()
for nom, mm, cuota in [('ORB solo, cuenta CFD (35 €/mes)', j.orb.values, 35.0), ('ORB + reversión, cuenta futuros (50 €/mes)', j.mezcla.values, 50.0),
                       ('ORB + reversión con la prima a la mitad (50 €/mes)', mh.values, 50.0)]:
    for perm in (None, 'obj10'):
        out, al, rd = b['sim'](mm, esc=0.45, perm=perm, cuota=cuota)
        print(f'{nom:52s} permanente {perm or "no":5s}: DARWIN {np.median(rd)*100:5.1f} %/año, asignaciones {al.mean():.1f}, neto {out.mean()/3:+7.0f} €/año, p10 36m {np.percentile(out,10):+7.0f}')
