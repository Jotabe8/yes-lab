"""EXPLORATORIO (no da veredicto): carry cripto V1 frente al tipo sin riesgo y en los últimos 12 meses."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, runpy
g = runpy.run_path("metodo/v4/carry_cripto.py", run_name="x")
R, V1, FUND, cartera = g["R"], g["V1"], g["FUND"], g["cartera"]
r, n = cartera(V1)
r = r[r.index >= "2020-03-01"]
tb = {2020: 0.4, 2021: 0.05, 2022: 2.0, 2023: 5.1, 2024: 5.0, 2025: 4.2, 2026: 3.8}  # letra 3 meses EE. UU., media anual aprox (%)
a = r.groupby(r.index.year).agg(lambda x: x.mean() * 365 * 100)
print("V1 anual % vs letras:", {y: f"{a[y]:+.1f} vs {tb[y]:.1f} → exceso {a[y]-tb[y]:+.1f}" for y in a.index})
u = r[r.index >= r.index[-1] - pd.Timedelta(days=365)]
print(f"últimos 12 meses: {u.mean()*365:+.2%}, días con posición {(n[u.index]>0).mean():.0%}")
f8 = (FUND / 3)[FUND.index >= FUND.index[-1] - pd.Timedelta(days=365)]
print("financiación media 12 meses (%/año) por moneda:", (f8.mean() * 3 * 365 * 100).round(1).sort_values().to_dict())
for um in (0.0002, 0.0003, 0.0005):
    est = g["regla"](um, 0.0)
    x, nn = cartera(est); x = x[x.index >= "2020-03-01"]; y = x[x.index >= x.index[-1] - pd.Timedelta(days=365)]
    print(f"umbral {um*100:.2f} %/8h: total {x.mean()*365:+.1%}/año, últimos 12 meses {y.mean()*365:+.2%}, días con posición {(nn[y.index]>0).mean():.0%} "
          f"(rendimiento en los días con posición {y[nn[y.index]>0].mean()*365 if (nn[y.index]>0).any() else 0:+.1%}/año)")
# Exceso sobre el efectivo: cuando la regla está fuera el dinero cobra la letra; cuando está dentro, no.
rf = pd.Series({pd.Timestamp(f"{y}-01-01"): v / 100 for y, v in tb.items()}).reindex(r.index, method="ffill") / 365
dentro = (n[r.index] > 0).astype(float)
exc = (r - rf) * dentro                     # lo que añade frente a dejar el dinero en letras
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
mitad = exc.index[len(exc) // 2]
print(f"EXCESO SOBRE LETRAS (solo días con posición): {exc.mean()*365:+.2%}/año t {t(exc):.2f} | 1ª {exc[:mitad].mean()*365:+.2%} 2ª {exc[mitad:].mean()*365:+.2%}")
print("  por año (%):", (exc.groupby(exc.index.year).mean() * 365 * 100).round(2).to_dict())
u = exc[exc.index >= exc.index[-1] - pd.Timedelta(days=365)]
print(f"  últimos 12 meses {u.mean()*365:+.2%}")
