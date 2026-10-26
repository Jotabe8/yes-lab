# Comprobación: ¿el EV negativo se debe al tope de riesgo de 1 %? Rejilla hasta 2 % en las mejores casillas.
import sys, numpy as np, pandas as pd
sys.argv = [sys.argv[0], sys.argv[1], "x"]
src = open("ev_ftmo.py").read().split("RISKS =")[0]; exec(src)
rows = []
for (grp, var, mc), (PC, PW, cal) in SER.items():
    if mc != 1.0 or not (var.startswith(("V0", "V1", "V4"))): continue
    for modo in ["cierre", "peor"]:
        W = PC if modo == "cierre" else PW
        for prod, size in [(2, 10), (2, 100), (1, 10)]:
            best = None
            for rc in [1.0, 1.5, 2.0, 3.0]:
                for rf in [0.5, 1.0, 1.5, 2.0]:
                    d = sim(PC, W, prod, size, rc, rf, N=3000)
                    if best is None or d["mean"] > best["mean"]: best = dict(d, rc=rc, rf=rf)
            rows.append(dict(grupo=grp, var=var[:2], modo=modo, prod=f"{prod}-Step", size=size, **best))
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/ev_riesgo_alto.csv", index=False)
pd.set_option("display.width", 250); print(D.round(1).to_string(index=False))
