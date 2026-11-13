import numpy as np, pandas as pd, sys
sys.path.insert(0, "estructura"); from comparar import emp, emp_f, R
rng = np.random.default_rng(3); n = 60_000
print("reto% fondeada%  pasa  EV/cuota  cobro_medio_si_pasa")
for fr in (0.015, 0.02, 0.025, 0.03, 0.04):
    a = emp(rng, n, fr, 0.10, R); b = a & emp(rng, n, fr, 0.05, R)
    for ff in (0.01, 0.015, 0.02, 0.025):
        c = np.where(b, emp_f(rng, n, ff, R), 0)
        print(f"{fr*100:4.1f} {ff*100:6.1f}  {b.mean():.3f} {c.mean()-540:8.0f} {c[b].mean():9.0f}")
