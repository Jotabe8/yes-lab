# P5: operaciones de referencia de la reversión con M1 (hora servidor = NY+7), con la MISMA lógica que ReversionDZ_v001.mq5:
# señal a las 15:58 NY con la sesión 9:30-15:57 (C = cierre de la vela 15:57), ayer = sesión completa 9:30-15:59,
# ATR20 = TR de hoy parcial + 19 sesiones completas, salida a las 15:58 si C > máximo de ayer o a las 5 sesiones.
# Uso: python referencia_m1.py <csv M1> <nombre> [<csv M1 adicional> ...]
import sys, numpy as np, pandas as pd
OFF = 7
def carga(rutas):
    ds = []
    for r in rutas:
        d = pd.read_csv(r, usecols=[0, 1, 2, 3, 4, 5]); d.columns = ['time', 'o', 'h', 'l', 'c', 'sp']
        d['time'] = pd.to_datetime(d.time); ds.append(d)
    d = pd.concat(ds).drop_duplicates('time', keep='last').sort_values('time')
    d['ny'] = d.time - pd.Timedelta(hours=OFF); d['dia'] = d.ny.dt.normalize(); d['hm'] = d.ny.dt.hour * 100 + d.ny.dt.minute
    return d[(d.hm >= 930) & (d.hm < 1600)]
def sesiones(m):
    g = m.groupby('dia')
    full = g.agg(H=('h', 'max'), L=('l', 'min'), C=('c', 'last'), ult=('hm', 'max'))
    p = m[m.hm < 1558].groupby('dia').agg(h0=('h', 'max'), l0=('l', 'min'), c0=('c', 'last'), u0=('hm', 'max'))
    s = full.join(p, how='inner')
    s['completa'] = s.ult >= 1555; s['senal_ok'] = s.u0 >= 1553
    sp = m[m.hm == 1557].groupby('dia').sp.last(); s['sp'] = sp
    return s
def ops(s, ibs=0.2, maxd=5, n_atr=20):
    s = s[s.completa | s.senal_ok].copy()
    dias = s.index; H, L, C = s.H.values, s.L.values, s.C.values
    h0, l0, c0, ok = s.h0.values, s.l0.values, s.c0.values, s.senal_ok.values; comp = s.completa.values
    tr_full = np.r_[np.nan, np.maximum(H[1:] - L[1:], np.maximum(abs(H[1:] - C[:-1]), abs(L[1:] - C[:-1])))]
    out = []; pos = None
    for i in range(n_atr + 1, len(s)):
        if not ok[i]: continue
        # ayer = sesión completa anterior
        k = i - 1
        while k >= 0 and not comp[k]: k -= 1
        if k < n_atr: continue
        if pos is not None:
            pos['ses'] += 1
            if c0[i] > H[k] or pos['ses'] >= maxd:
                out.append((pos['dia'], dias[i], pos['ses'], pos['pe'], c0[i], (c0[i] - pos['pe']) / pos['atr'], pos['sp'] / pos['atr'])); pos = None
            continue
        if h0[i] <= l0[i]: continue
        if (c0[i] - l0[i]) / (h0[i] - l0[i]) < ibs and c0[i] < C[k]:
            prev = [j for j in range(k, -1, -1) if comp[j]][:n_atr]
            if len(prev) < n_atr: continue
            tr0 = max(h0[i] - l0[i], abs(h0[i] - C[k]), abs(l0[i] - C[k]))
            trs = [tr0] + [max(H[j] - L[j], abs(H[j] - C[pj]), abs(L[j] - C[pj])) for j, pj in zip(prev[:-1], prev[1:])]
            atr = np.mean(trs[:n_atr]) if len(trs) >= n_atr else np.mean(trs)
            pos = dict(dia=dias[i], pe=c0[i], atr=atr, ses=0, sp=s.sp.values[i] if not np.isnan(s.sp.values[i]) else 0)
    return pd.DataFrame(out, columns=['entrada', 'salida', 'sesiones', 'p_ent', 'p_sal', 'r_bruto', 'spread_r'])
if __name__ == '__main__':
    nombre = sys.argv[2]; m = carga([sys.argv[1]] + sys.argv[3:]); s = sesiones(m); o = ops(s)
    t = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x))
    o.to_csv(f'ops_ref_{nombre}.csv', index=False)
    n = o.r_bruto - o.spread_r
    print(f'{nombre}: {s.index.min().date()}→{s.index.max().date()} n={len(o)} bruto {o.r_bruto.mean():+.3f} R t {t(o.r_bruto):.2f} | '
          f'spread {o.spread_r.mean():.3f} R | neto {n.mean():+.3f} t {t(n):.2f} | 2023+ {n[o.entrada >= "2023"].mean():+.3f} (n={int((o.entrada >= "2023").sum())})')
