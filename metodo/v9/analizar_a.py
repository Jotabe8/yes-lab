"""Ejecuta el preregistro v9-A y escribe salida_a.txt."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, ".")
import eventos as E

ev = pd.read_csv("eventos.csv")
out = []
def p(*a):
    s = " ".join(str(v) for v in a); print(s); out.append(s)

def resumen(o, nombre):
    o = o.copy(); o["neto"] = o.rb - o.coste; o["neto2"] = o.rb - 2 * o.coste
    m, t, n = E.t_dia(o); m2, t2, _ = E.t_dia(o, "neto2"); mb, tb, _ = E.t_dia(o, "rb")
    a = o[o.fecha < "2019-01-01"]; b = o[o.fecha >= "2019-01-01"]
    p(f"{nombre}: ops {len(o)} días {n} | bruto {mb:+.3f} (t {tb:.2f}) coste {o.coste.mean():.3f} | "
      f"neto {m:+.3f} (t {t:.2f}) | ×2 {m2:+.3f} | 2011-18 {E.t_dia(a)[0]:+.3f} 2019-26 {E.t_dia(b)[0]:+.3f}")
    return o

V = {"V1": dict(k_stop=0.15, salida=180), "V2": dict(k_stop=0.15, salida=60), "V3": dict(k_stop=0.30, salida=180)}
res = {}
for v, kw in V.items():
    res[v] = resumen(E.tabla(ev, **kw), v)
o = res["V1"]
p("\nV1 por mercado:")
for s, g in o.groupby("sim"): resumen(g, "  " + s)
p("V1 por evento:")
for s, g in o.groupby("evento"): resumen(g, "  " + s)
p("\nPlacebo de lado (V1 contraria):"); resumen(E.tabla(ev, lado=-1), "  contraria")
p("Placebo de hora (misma regla, días sin evento):")
pl = resumen(E.tabla(ev, dias="placebo"), "  placebo")
d = o.groupby("fecha").neto.mean(); dp = pl.groupby("fecha").neto.mean()
dif = d.mean() - dp.mean(); se = np.sqrt(d.var() / len(d) + dp.var() / len(dp))
p(f"  diferencia evento − placebo {dif:+.3f} (t {dif / se:.2f})")
o.to_csv("ops_a_v1.csv", index=False)
open("salida_a.txt", "w").write("\n".join(out) + "\n")
