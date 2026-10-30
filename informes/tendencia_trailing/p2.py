# P2 de la variante 100/4/solo largos (la única de las 18 que supera el p95 del placebo en ajuste).
import numpy as np, pandas as pd
from tendencia import preparar, correr, periodo, t_stat, INI, FIN_AJUSTE
M = preparar()
ops, dia = correr(M, 100, 4.0, True); opf, _ = correr(M, 100, 4.0, True, "ftmo")
o = periodo(ops, INI, FIN_AJUSTE); of = periodo(opf, INI, FIN_AJUSTE)
def lin(nombre, x, xf=None):
    s = f"{nombre:28s} ops {len(x):5d}  bruto {x.r_bruto.mean():+.3f}  neto {x.r_neto.mean():+.3f} (t {t_stat(x.r_neto):.2f})"
    s += f"  costes x2 {(x.r_bruto - 2*(x.c_spread + x.c_fin)).mean():+.3f}"
    if xf is not None: s += f"  FTMO {xf.r_neto.mean():+.3f}  FTMO x2 {(xf.r_bruto - 2*(xf.c_spread + xf.c_fin)).mean():+.3f}"
    print(s)
lin("cesta", o, of)
lin("sin cripto", o[o.grupo != "cripto"], of[of.grupo != "cripto"])
lin("sin cripto ni agrícolas", o[~o.grupo.isin(["cripto", "agricolas"])], of[~of.grupo.isin(["cripto", "agricolas"])])
for g in sorted(o.grupo.unique()): lin("  " + g, o[o.grupo == g], of[of.grupo == g])
print("\nPor año (sin cripto, neto normal / FTMO):")
x = o[o.grupo != "cripto"].groupby(o.entrada.dt.year).r_neto.agg(["count", "mean"])
x["ftmo"] = of[of.grupo != "cripto"].groupby(of.entrada.dt.year).r_neto.mean()
print(x.round(3).T.to_string()); print("años positivos:", (x["mean"] > 0).mean().round(2), "FTMO:", (x.ftmo > 0).mean().round(2))
print("\nMeseta (solo largos, sin cripto, neto normal / FTMO):")
for N in (80, 100, 120):
    for TR in (3.5, 4.0, 4.5):
        a, _ = correr(M, N, TR, True); b, _ = correr(M, N, TR, True, "ftmo")
        a = periodo(a, INI, FIN_AJUSTE); b = periodo(b, INI, FIN_AJUSTE)
        a = a[a.grupo != "cripto"]; b = b[b.grupo != "cripto"]
        print(f"  {N:3d}/{TR}: ops {len(a)} neto {a.r_neto.mean():+.3f} t {t_stat(a.r_neto):.2f}  FTMO {b.r_neto.mean():+.3f}")
