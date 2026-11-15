import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import eventos as E
SIG = {"EURUSD": 1, "GBPUSD": 1, "USDJPY": -1, "XAUUSD": 1}
T0, T1 = 75, 595       # 8:15 y 16:55 NY
fil = []
for s, sg in SIG.items():
    fe, x, _ = E.cargar(s)
    e, sx = x[:, T0, 0], x[:, T1, 0]
    ok = np.isfinite(e) & np.isfinite(sx)
    pb = sg * (sx - e) / e * 1e4
    co = (x[:, T0, 4] / 2 + x[:, T1, 4] / 2) / e * 1e4 + E.COMISION[s] * 1e4
    for f, a, c in zip(fe[ok], pb[ok], co[ok]):
        fil.append((f, s, a, c))
o = pd.DataFrame(fil, columns=["fecha", "sim", "bruto", "coste"]); o["neto"] = o.bruto - o.coste; o["neto2"] = o.bruto - 2 * o.coste
o["placebo"] = -o.bruto - o.coste
out = []
def r(g, n):
    for col in ("bruto", "neto", "neto2", "placebo"):
        d = g.groupby("fecha")[col].mean()
        out.append(f"{n:10s} {col:8s} {d.mean():+7.2f} pb  t {d.mean()/d.std()*np.sqrt(len(d)):+5.2f}  días {len(d)}")
r(o, "todo"); r(o[o.fecha < "2020-01-01"], "2011-19"); r(o[o.fecha >= "2020-01-01"], "2020-26")
for s, g in o.groupby("sim"): r(g, s)
print("\n".join(out)); open("salida_fix_usd.txt", "w").write("\n".join(out) + "\n")
