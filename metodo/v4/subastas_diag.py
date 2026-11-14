"""Diagnóstico informativo del candidato 8 (no cambia el veredicto preregistrado)."""
import numpy as np, pandas as pd, runpy, io, contextlib
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path("metodo/v4/subastas.py")
t, correr, f_all, pos, r, n1 = g["t"], g["correr"], g["f_all"], g["pos"], g["r"], g["n1"]
print(f"posición media {pos.mean():+.2f} (largo {(pos>0).mean():.0%}, corto {(pos<0).mean():.0%}); IEF comprado siempre {r.mean()*252:+.2%}/año")
vol = n1.std() * np.sqrt(252); esc = 0.15 / vol; e = n1 * esc; eq = e.cumsum(); dd = (eq - eq.cummax()).min()
print(f"vol {vol:.1%}; a 15 % vol: {e.mean()*252:+.1%}/año, DD máx {dd:.1%} (= {abs(dd)/(e.mean()*252):.1f}× el beneficio anual), Sharpe {e.mean()/e.std()*np.sqrt(252):.2f}")
for a, b in (("2002", "2008"), ("2009", "2015"), ("2016", "2020"), ("2021", "2026")):
    x = n1[a:b]; print(f"   {a}-{b}: {x.mean()*252:+.2%}/año t {t(x):.2f}")
posA, _, nA = correr("IEF", "IEF", f_all, pre=False)
rng = np.random.default_rng(7); pl = []
for i in range(200):
    k = int(rng.integers(20, len(posA) - 20)); ps = pd.Series(np.roll(posA.values, k), posA.index)
    pl.append((ps * r - ps.diff().abs().fillna(0) * 0.0001).mean())
print(f"pata posterior (largo) vs su placebo de rotación: {nA.mean()*252:+.2%} vs p95 {np.percentile(pl,95)*252:+.2%} (media {np.mean(pl)*252:+.2%})")
# largo los días SIN subasta reciente (complemento) para comparar con la deriva
comp = ((posA == 0) * r); print(f"largo el resto de días: {comp.mean()*252:+.2%}/año t {t(comp):.2f}")
