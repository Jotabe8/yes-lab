"""v16 fase 1 — 5 sistemas aleatorios en los 5 mercados aleatorios + 2.000 aleatorios por mercado.

Cada sistema se sortea con semilla registrada (20261120 + i): vela de entrada al azar entre las
horas líquidas, duración H, stop k·ATR14 y una regla de dirección sacada de una lista de rasgos
medidos antes de entrar (seguir/contrariar). Se mide en exploración (2018-22) y fuera (2023-26).

Objetivo: (1) línea base de qué da el azar tras costes; (2) cuánto «parece» ganar el mejor de
N aleatorios elegido en exploración y qué hace después (sesgo de selección medido, no supuesto).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from metodo.embudo import t_agrupado
from metodo.v16.datos import MERCADOS, NOMBRE, SEMILLA, cargar
from metodo.v16.motor import Mercado, horas_liquidas

REGLAS = ['largo', 'corto', 'sigue_r1h', 'contra_r1h', 'sigue_rdia', 'contra_rdia',
          'sigue_rayer', 'contra_rayer', 'sigue_posrango', 'contra_posrango']
HS = [6, 12, 24, 36, 48, 72]


def sortear(rng, M, liq):
    H = int(rng.choice(HS))
    cand = liq[(liq >= 12) & (liq + H <= 288)]
    cand = cand[np.isin(cand + H - 1, liq)]  # que la salida también caiga en hora líquida
    b = int(rng.choice(cand))
    k = float(np.round(rng.uniform(0.2, 1.0), 2))
    regla = str(rng.choice(REGLAS))
    return dict(b=b, H=H, k=k, regla=regla)


def direccion(M, s):
    n = len(M.O)
    r = s['regla']
    if r == 'largo':
        return np.ones(n)
    if r == 'corto':
        return -np.ones(n)
    modo, rasgo = r.split('_')
    x = M.rasgo(rasgo, s['b'])
    if rasgo == 'posrango':
        x = x - 0.5
    d = np.sign(x)
    d[~np.isfinite(d)] = 0
    return d if modo == 'sigue' else -d


def evaluar(M, s):
    R, c = M.operar(s['b'], s['H'], s['k'], direccion(M, s))
    ok = np.isfinite(R)
    semana = pd.to_datetime(M.dias.astype(str)).to_period('W').astype(str).to_numpy()
    res = {}
    for nom, mk in (('exp', M.exp), ('oos', ~M.exp)):
        m = ok & mk
        neto = R[m] - c[m]
        res[nom] = dict(n=int(m.sum()), bruto=float(np.mean(R[m])), coste=float(np.mean(c[m])),
                        neto=float(np.mean(neto)), t=t_agrupado(neto, semana[m]),
                        t_bruto=t_agrupado(R[m], semana[m]))
    return res


def hora(b):
    return f'{b * 5 // 60:02d}:{b * 5 % 60:02d}'


def main(n_null=2000):
    filas, nulos = [], []
    for i, m in enumerate(MERCADOS):
        d, x = cargar(m)
        M = Mercado(m, d, x)
        liq = horas_liquidas(M)
        s = sortear(np.random.default_rng(SEMILLA + i), M, liq)
        r = evaluar(M, s)
        filas.append(dict(sistema=i + 1, mercado=NOMBRE[m], entrada_utc=hora(s['b']), H_min=s['H'] * 5,
                          k_atr=s['k'], regla=s['regla'],
                          **{f'{p}_{q}': round(v, 4) for p in r for q, v in r[p].items()}))
        rng = np.random.default_rng(SEMILLA * 10 + i)
        for j in range(n_null):
            sj = sortear(rng, M, liq)
            rj = evaluar(M, sj)
            nulos.append(dict(mercado=NOMBRE[m], j=j, **sj,
                              **{f'{p}_{q}': v for p in rj for q, v in rj[p].items()}))
        print(m, 'hecho', file=sys.stderr, flush=True)
    return pd.DataFrame(filas), pd.DataFrame(nulos)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    f, nu = main(n)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
    print('=== Los 5 sistemas aleatorios (R por operación; t por semana) ===')
    print(f[['sistema', 'mercado', 'entrada_utc', 'H_min', 'k_atr', 'regla', 'exp_n', 'exp_bruto', 'exp_coste',
             'exp_neto', 'exp_t', 'oos_n', 'oos_bruto', 'oos_neto', 'oos_t']].to_string(index=False))
    nu.to_csv('metodo/v16/salidas/nulos_aleatorios.csv.gz', index=False)
    print(f'\n=== {n} aleatorios por mercado ===')
    for mk, g in nu.groupby('mercado'):
        print(f"{mk}: bruto exp medio {g.exp_bruto.mean():+.4f} R | neto exp medio {g.exp_neto.mean():+.4f} R | "
              f"coste medio {g.exp_coste.mean():.4f} R | % neto>0 exp {100 * (g.exp_neto > 0).mean():.1f} % | "
              f"% t_exp>2 {100 * (g.exp_t > 2).mean():.1f} % | t_bruto exp p5/p50/p95 "
              f"{g.exp_t_bruto.quantile(.05):+.2f}/{g.exp_t_bruto.median():+.2f}/{g.exp_t_bruto.quantile(.95):+.2f}")
    print('\n=== Sesgo de selección: el mejor de N por t neto en exploración, ¿qué hace fuera? ===')
    for N in (5, 20, 100, 500, 2000):
        res = []
        rng = np.random.default_rng(7)
        for _ in range(200):
            idx = rng.choice(len(nu), N, replace=False)
            g = nu.iloc[idx]
            mej = g.loc[g.exp_t.idxmax()]
            res.append((mej.exp_t, mej.exp_neto, mej.oos_neto, mej.oos_t))
        res = np.array(res)
        print(f'N={N:5d}: t exp del mejor {res[:, 0].mean():.2f} | neto exp {res[:, 1].mean():+.4f} R | '
              f'neto OOS {res[:, 2].mean():+.4f} R | t OOS {res[:, 3].mean():+.2f} | % OOS>0 {100 * (res[:, 2] > 0).mean():.0f} %')
    # correlación entre t de exploración y t fuera en toda la población
    print(f"\ncorr(t exp, t OOS) entre los {len(nu)} aleatorios: {np.corrcoef(nu.exp_t, nu.oos_t)[0, 1]:+.3f}")
    print(f"corr(t_bruto exp, t_bruto OOS): {np.corrcoef(nu.exp_t_bruto, nu.oos_t_bruto)[0, 1]:+.3f}")
