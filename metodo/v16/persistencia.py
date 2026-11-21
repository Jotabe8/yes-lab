"""¿Persiste el mapa entero? t de exploración frente a t de 2023-26 en las 4.628 celdas (mismos cortes)."""
import numpy as np, pandas as pd
from metodo.v16.fase2_mapa import mapa, preparar
from metodo.v16.datos import NOMBRE
Ms, celdas = preparar()
e = mapa(Ms, celdas); o = mapa(Ms, celdas, exp=False)
d = e[['m', 'b', 'H', 'rasgo', 'lado', 't', 'media', 'coste']].copy(); d['t_oos'] = o.t.values; d['media_oos'] = o.media.values
d = d.dropna(subset=['t', 't_oos'])
print(f'celdas {len(d)} | corr(t exp, t oos) {np.corrcoef(d.t, d.t_oos)[0,1]:+.3f}')
for u in (2, 3, 4):
    s = d[d.t.abs() >= u]
    adj = np.sign(s.t) * s.t_oos
    ef = (np.sign(s.t) * s.media_oos / s.coste)
    print(f'|t exp|>={u}: {len(s)} celdas | mismo signo fuera {100*(adj>0).mean():.0f} % | t fuera medio (con signo) {adj.mean():+.2f} | '
          f'efecto fuera medio {ef.mean():+.2f}× coste | con |t fuera|>=2 mismo signo: {(adj>=2).sum()}')
for m, g in d.groupby('m'):
    s = g[g.t.abs() >= 3]
    print(NOMBRE[m], f'corr {np.corrcoef(g.t, g.t_oos)[0,1]:+.3f}', f'|t|>=3: {len(s)}, mismo signo {100*((np.sign(s.t)*s.t_oos)>0).mean() if len(s) else float("nan"):.0f} %')
tod = d[d.rasgo == 'todos']
print(f"solo 'todos los días' (reloj puro): corr {np.corrcoef(tod.t, tod.t_oos)[0,1]:+.3f}")
for m, g in tod.groupby('m'):
    print('  reloj', NOMBRE[m], f'corr {np.corrcoef(g.t, g.t_oos)[0,1]:+.3f}')
d.to_csv('metodo/v16/salidas/persistencia.csv.gz', index=False)
