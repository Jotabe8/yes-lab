"""v16 fase 3 — confirmación 2023-26 de las 4 candidatas preregistradas (PREREGISTRO.md). Una vez."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from metodo.embudo import t_agrupado
from metodo.v16.datos import cargar
from metodo.v16.motor import Mercado, horas_liquidas

CORTES = json.load(open('metodo/v16/salidas/cortes_v16.json'))
K_STOP = 0.5
CAND = {
    'C1': dict(m='EURUSD', b=18, H=12, rasgo='posrango', lado=+1, corte='C1'),
    'C2': dict(m='EURUSD', b=72, H=12, rasgo='rayer', lado=-1, corte='C2'),
    'C3': dict(m='EURUSD', b=108, H=36, rasgo=None, lado=-1, corte=None),
    'C4': dict(m='XAUUSD', b=78, H=12, rasgo='rayer', lado=+1, corte='C4'),
}


def regla(M, c, b):
    n = len(M.O)
    if c['rasgo'] is None:
        sel = np.ones(n, bool)
    else:
        x = M.rasgo(c['rasgo'], b)
        q1 = CORTES[c['corte']]['q1'] if b == c['b'] or c['rasgo'] == 'rayer' else np.nanquantile(x[M.exp], 1 / 3)
        sel = np.isfinite(x) & (x <= q1)
    return np.where(sel, c['lado'], 0)


def medir(M, c, b, mk):
    R, cR = M.operar(b, c['H'], K_STOP, regla(M, c, b))
    sem = pd.to_datetime(M.dias.astype(str)).to_period('W').astype(str).to_numpy()
    ok = np.isfinite(R) & mk
    neto = R[ok] - cR[ok]
    return dict(n=int(ok.sum()), bruto=R[ok].mean(), coste=cR[ok].mean(), neto=neto.mean(),
                t=t_agrupado(neto, sem[ok]), neto2=(R[ok] - 2 * cR[ok]).mean(),
                R=R, cR=cR, ok=ok)


if __name__ == '__main__':
    Ms = {}
    filas = []
    diarias = {}
    for k, c in CAND.items():
        M = Ms.setdefault(c['m'], Mercado(c['m'], *cargar(c['m'])))
        oos = ~M.exp
        e = medir(M, c, c['b'], M.exp)
        o = medir(M, c, c['b'], oos)
        a1 = oos & (M.dias < 20250101); a2 = oos & (M.dias >= 20250101)
        h1, h2 = medir(M, c, c['b'], a1), medir(M, c, c['b'], a2)
        # placebo de hora
        liq = set(horas_liquidas(M).tolist())
        plac = []
        for b in sorted(liq):
            if b == c['b'] or b < 12 or b + c['H'] > 288 or (b + c['H'] - 1) not in liq:
                continue
            plac.append(medir(M, c, b, oos)['t'])
        p95 = float(np.quantile(plac, 0.95)); pval = float(np.mean(np.array(plac) >= o['t']))
        años = (M.dias[oos].max() // 10000 - 2023) + (M.dias[oos].max() // 100 % 100) / 12
        puertas = dict(t=o['t'] >= 2.24, doble=o['neto2'] > 0, mitades=(h1['neto'] > 0) and (h2['neto'] > 0),
                       placebo=o['t'] > p95)
        filas.append(dict(id=k, mercado=c['m'], n_exp=e['n'], neto_exp=round(e['neto'], 4), t_exp=round(e['t'], 2),
                          n_oos=o['n'], ops_año=round(o['n'] / años, 0), bruto_oos=round(o['bruto'], 4),
                          coste_oos=round(o['coste'], 4), neto_oos=round(o['neto'], 4), t_oos=round(o['t'], 2),
                          neto_x2=round(o['neto2'], 4), neto_23_24=round(h1['neto'], 4), neto_25_26=round(h2['neto'], 4),
                          placebo_p95=round(p95, 2), p_placebo=round(pval, 3), n_placebo=len(plac),
                          decae=round(o['bruto'] / e['bruto'], 2) if e['bruto'] else np.nan,
                          PASA=all(puertas.values()), **{f'g_{q}': v for q, v in puertas.items()}))
        r = np.where(o['ok'], o['R'] - o['cR'], np.nan)
        diarias[k] = pd.Series(r, index=pd.to_datetime(M.dias.astype(str)))
    f = pd.DataFrame(filas)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
    print('=== Confirmación 2023-26 (R con stop 0,5·ATR14; t por semana) ===')
    print(f.T.to_string(header=False))
    d = pd.DataFrame(diarias)
    print('\ncorrelación diaria de R neta fuera de muestra:')
    print(d.corr().round(2).to_string())
    d.to_csv('metodo/v16/salidas/oos_diario.csv')
