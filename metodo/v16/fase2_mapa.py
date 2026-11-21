"""v16 fase 2 — mapa de exploración 2018-22 con nulo por permutación (protocolo fijado antes de correr).

Espacio de búsqueda (TODO lo que se mira cuenta):
  5 mercados × velas de entrada cada 30 min en horas líquidas (desde la 1.ª hora) × H ∈ {1 h, 3 h}
  (salida también en hora líquida) × 13 condiciones: todos los días + 6 rasgos × {tercio alto,
  tercio bajo}. Rasgos medidos antes de entrar: r1h (última hora), rdia (desde las 00 UTC),
  rayer (día anterior), volsorpresa (vol. última hora / su media 20 días a esa hora),
  posrango (posición en el rango de ayer), cruzado1h (r1h medio z de los otros 4 mercados).
  Cortes de tercio con datos de exploración. Dirección = signo de la media (dos colas).
Estadístico: rendimiento medio (precio medio) de la apertura de b al cierre de b+H−1; t con
  errores por semana. Descubrimiento: |t| ≥ umbral FWER 5 % del nulo y |media| ≥ 2× coste.
Nulo: 30 repeticiones del mapa entero con (a) el rasgo permutado entre días dentro de cada
  mercado y vela, y (b) para «todos los días», signo aleatorio por día. El máximo |t| de cada
  repetición da el umbral FWER; el nº medio de «descubrimientos» del nulo se compara con el real.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from metodo.v16.datos import MERCADOS, NOMBRE, cargar
from metodo.v16.motor import RASGOS, Mercado, cruzar, horas_liquidas

HS = [12, 36]


def t_semana(x, sem):
    ok = np.isfinite(x)
    x, sem = x[ok], sem[ok]
    if len(x) < 30:
        return np.nan, np.nan, 0
    m = x.mean()
    dev = pd.Series(x - m).groupby(sem).sum().to_numpy()
    se = np.sqrt(np.sum(dev ** 2)) / len(x)
    return m, (m / se if se > 0 else np.nan), len(x)


def preparar():
    Ms = {m: Mercado(m, *cargar(m)) for m in MERCADOS}
    barras = range(12, 288, 6)
    cruzar(Ms, barras)
    celdas = []  # (m, b, H, rasgo, lado, máscara de días, fwd)
    for m, M in Ms.items():
        liq = set(horas_liquidas(M).tolist())
        sem = pd.to_datetime(M.dias.astype(str)).to_period('W').astype(str).to_numpy()
        M.sem = sem
        for b in barras:
            if b not in liq:
                continue
            R = {r: M.rasgo(r, b) for r in RASGOS}
            for H in HS:
                if b + H > 288 or (b + H - 1) not in liq:
                    continue
                f = M.adelante(b, H)
                celdas.append(dict(m=m, b=b, H=H, f=f, R=R))
    return Ms, celdas


def mapa(Ms, celdas, rng=None, exp=True):
    """Devuelve DataFrame de pruebas. Con rng: versión nula (permutación / signo aleatorio)."""
    out = []
    for c in celdas:
        M = Ms[c['m']]
        mk = M.exp if exp else ~M.exp
        f = c['f'].copy()
        sem = M.sem
        coste = M.coste
        # todos los días
        g = f[mk]
        if rng is not None:
            g = g * rng.choice([-1, 1], len(g))
        mu, t, n = t_semana(g, sem[mk])
        out.append((c['m'], c['b'], c['H'], 'todos', '', mu, t, n, coste))
        for r in RASGOS:
            x = c['R'][r]
            xe = x[M.exp]
            if np.isfinite(xe).sum() < 100:
                continue
            q1, q2 = np.nanquantile(xe, [1 / 3, 2 / 3])
            xm = x[mk].copy()
            if rng is not None:
                fin = np.isfinite(xm)
                xm[fin] = rng.permutation(xm[fin])
            for lado, sel in (('bajo', xm <= q1), ('alto', xm >= q2)):
                mu, t, n = t_semana(np.where(sel, f[mk], np.nan), sem[mk])
                out.append((c['m'], c['b'], c['H'], r, lado, mu, t, n, coste))
    df = pd.DataFrame(out, columns=['m', 'b', 'H', 'rasgo', 'lado', 'media', 't', 'n', 'coste'])
    df['efecto_x_coste'] = df.media.abs() / df.coste
    return df


def hora(b):
    return f'{b * 5 // 60:02d}:{b * 5 % 60:02d}'


if __name__ == '__main__':
    n_nulo = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    Ms, celdas = preparar()
    real = mapa(Ms, celdas)
    real.to_csv('metodo/v16/salidas/mapa_exploracion.csv.gz', index=False)
    print(f'pruebas en el mapa: {len(real)}  (celdas m×b×H: {len(celdas)})')
    maxs, cuentas, cuentas3 = [], [], []
    for k in range(n_nulo):
        nu = mapa(Ms, celdas, rng=np.random.default_rng(1000 + k))
        maxs.append(np.nanmax(np.abs(nu.t)))
        cuentas.append(int(((nu.t.abs() >= 3) & (nu.efecto_x_coste >= 2)).sum()))
        cuentas3.append(int((nu.t.abs() >= 3).sum()))
        print(f'nulo {k}: max|t| {maxs[-1]:.2f}  |t|>=3: {cuentas3[-1]}  (+efecto>=2x coste: {cuentas[-1]})',
              file=sys.stderr, flush=True)
    u = float(np.quantile(maxs, 0.95))
    print(f'umbral FWER 5 % (p95 del max|t| nulo): {u:.2f}  | max|t| nulo medio {np.mean(maxs):.2f}')
    print(f'|t|>=3 → real {int((real.t.abs() >= 3).sum())} vs nulo medio {np.mean(cuentas3):.1f} (p95 {np.quantile(cuentas3, .95):.0f})')
    print(f'|t|>=3 y efecto>=2×coste → real {int(((real.t.abs() >= 3) & (real.efecto_x_coste >= 2)).sum())} '
          f'vs nulo medio {np.mean(cuentas):.1f} (p95 {np.quantile(cuentas, .95):.0f})')
    real['hora'] = real.b.map(hora)
    real['mercado'] = real.m.map(NOMBRE)
    top = real[real.efecto_x_coste >= 2].reindex(real[real.efecto_x_coste >= 2].t.abs().sort_values(ascending=False).index).head(40)
    pd.set_option('display.width', 250)
    print('\n=== 40 mejores |t| con efecto ≥ 2× coste (exploración 2018-22) ===')
    print(top[['mercado', 'hora', 'H', 'rasgo', 'lado', 'n', 'media', 't', 'efecto_x_coste']].to_string(index=False))
    print('\n=== Recuento por rasgo de |t|>=3 (real) ===')
    print(real[real.t.abs() >= 3].groupby(['rasgo']).size().to_string())
    print('\n=== Recuento por mercado de |t|>=3 (real) ===')
    print(real[real.t.abs() >= 3].groupby(['mercado']).size().to_string())
    np.save('metodo/v16/salidas/nulo_max_t.npy', np.array(maxs))
