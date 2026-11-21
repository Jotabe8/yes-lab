"""v18: descripción de la caída del S&P 500 (16-20 nov 2026) y comparación histórica. No es una prueba."""
import numpy as np, pandas as pd
D = 'datos'
def dia(n):
    return pd.read_csv(f'{D}/d_{n}.csv', parse_dates=['Date']).set_index('Date').dropna(subset=['Close'])
g = dia('GSPC'); v = dia('VIX'); n = dia('NDX'); j = dia('DJI')
print('=== Semana 16-20 nov 2026 (cierres) ===')
for k, d in (('S&P 500', g), ('Nasdaq-100', n), ('Dow', j)):
    c = d.Close; w = c.loc['2026-11-13':'2026-11-20']
    print(f"{k}: " + ' '.join(f"{i:%d}:{r*100:+.2f}%" for i, r in w.pct_change().dropna().items()),
          f"| semana {(w.iloc[-1]/w.iloc[0]-1)*100:+.2f}% | desde máx. {(c.iloc[-1]/c.cummax().iloc[-1]-1)*100:+.2f}% (máx {c.idxmax():%d-%m-%Y})")
tr = pd.concat([g.High - g.Low, (g.High - g.Close.shift()).abs(), (g.Low - g.Close.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(20).mean().shift()
print('Rango verdadero / ATR20 previo:', ' '.join(f"{i:%d}:{x:.2f}" for i, x in (tr / atr).loc['2026-11-16':].items()))
print('VIX:', ' '.join(f"{i:%d}:{x:.1f}" for i, x in v.Close.loc['2026-11-13':].items()))
r = np.log(g.Close).diff()
vol20 = r.rolling(20).std() * np.sqrt(252) * 100
print(f"Vol realizada 5 días anualizada {r.loc['2026-11-16':].std()*np.sqrt(252)*100:.1f} % | 20 días {vol20.iloc[-1]:.1f} % | mediana 1990-2026 {vol20.loc['1990':].median():.1f} %")

print('\n=== Intradía US500 (Dukascopy, barras 30 min, % de cada media hora) ===')
b = pd.read_csv(f'{D}/US500_b30_nov.csv', parse_dates=['fecha'])
b = b[b.fecha >= '2026-11-16']
for f, x in b.groupby('fecha'):
    x = x.sort_values('bar'); ret = (x.c / x.o.iloc[0] - 1) * 100
    print(f"{f:%a %d}: 9:30→10:00 {(x.c.iloc[0]/x.o.iloc[0]-1)*100:+.2f}% | 10:00→16:00 {(x.c.iloc[-1]/x.c.iloc[0]-1)*100:+.2f}% |"
          f" 15:00→16:00 {(x.c.iloc[-1]/x.c.iloc[-3]-1)*100:+.2f}% | sesión {(x.c.iloc[-1]/x.o.iloc[0]-1)*100:+.2f}% | mín. en barra {x.l.idxmin()-x.index[0]} | horquilla {x.spr.mean():.2f} pts")
# hueco (cierre ayer 16:00 → apertura 9:30) vs sesión
bb = pd.read_csv(f'{D}/US500_b30_nov.csv', parse_dates=['fecha'])
o = bb[bb.bar == 0].set_index('fecha').o; c = bb[bb.bar == 12].set_index('fecha').c
s = pd.DataFrame({'noche': (o / c.shift() - 1) * 100, 'sesion': (c / o - 1) * 100}).loc['2026-11-16':]
print('Noche vs sesión (%):'); print(s.round(2).to_string())
print(f"Suma semana: noche {s.noche.sum():+.2f} %, sesión {s.sesion.sum():+.2f} %")

print('\n=== Comparación histórica S&P 500 (desde 1950): caídas de 5 sesiones ≤ −7 % ===')
c = g.Close; r5 = c / c.shift(5) - 1
ev = []; ult = None
for i in np.where(r5 <= -0.07)[0]:
    if ult is not None and i - ult < 20: continue
    # primer día del episodio: tomar el mínimo de r5 en los 10 días siguientes
    k = i + int(np.argmin(r5.iloc[i:i + 10].values)); ult = k
    dd = c.iloc[k] / c.iloc[:k + 1].iloc[-252:].max() - 1
    f = lambda h: (c.iloc[k + h] / c.iloc[k] - 1) * 100 if k + h < len(c) else np.nan
    mn = (c.iloc[k:k + 61].min() / c.iloc[k] - 1) * 100
    vx = v.Close.get(c.index[k], np.nan)
    ev.append((c.index[k].date(), r5.iloc[k] * 100, dd * 100, vx, f(5), f(20), f(60), mn))
e = pd.DataFrame(ev, columns=['fecha', 'r5_%', 'desde_max_1a_%', 'VIX', 'sig5_%', 'sig20_%', 'sig60_%', 'min_60s_%'])
print(e.round(1).to_string(index=False))
h = e.iloc[:-1] if str(e.fecha.iloc[-1]) >= '2026-11-01' else e
print(f"\nEpisodios anteriores: {len(h)} | siguiente 5 s: mediana {h['sig5_%'].median():+.1f} % (>0 {(h['sig5_%']>0).mean()*100:.0f} %) | 20 s: "
      f"{h['sig20_%'].median():+.1f} % (>0 {(h['sig20_%']>0).mean()*100:.0f} %) | 60 s: {h['sig60_%'].median():+.1f} % (>0 {(h['sig60_%']>0).mean()*100:.0f} %)"
      f" | caída extra media hasta 60 s {h['min_60s_%'].mean():.1f} %")
# base: todas las ventanas de 20 sesiones
b20 = (c.shift(-20) / c - 1).loc['1950':] * 100
print(f"Base cualquier día: 20 s mediana {b20.median():+.1f} % (>0 {(b20>0).mean()*100:.0f} %)")
print('\nNota: n pequeño y episodios solapados con crisis (1987, 2008, 2020); es contexto, no regla.')
