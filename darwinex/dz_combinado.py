# DARWIN de futuros en Darwinex Zero: ORB US100 (NQ) solo frente a ORB US100 + ORB cripto (BTC+ETH CME estándar).
# Mismo Monte Carlo que darwinex-senales/dz_sim.py. Ventana común 2021-03 → 2026-10. Darwinex reescala el DARWIN a VaR
# objetivo, así que la mezcla se normaliza a la misma volatilidad mensual que el ORB solo (1 R = 0,45 %).
import numpy as np, pandas as pd, importlib.util, sys, os, io, contextlib
spec = importlib.util.spec_from_file_location("b", "dz_sim_base.py"); b = importlib.util.module_from_spec(spec)
src = open("dz_sim_base.py").read().split("filas=[]")[0].replace("../dos-orb/serie_v018_be.csv", "/mnt/project-files/dos-orb/serie_v018_be.csv")
exec(src, b.__dict__)
o = b.s.Rbe - 0.05
c = pd.read_csv("cripto_cartera_diaria.csv", parse_dates=["fecha"]).set_index("fecha").R
om = o["2021-03":"2026-10"].resample("ME").sum(); cm = c["2021-03":"2026-10"].resample("ME").sum()
j = pd.concat([om, cm], axis=1, keys=["o", "c"], sort=True).fillna(0)
mix = j.o + j.c * (j.o.std() / j.c.std()); mix = mix * (j.o.std() / mix.std())
for nom, mm, cuota in [("ORB US100 solo (CFD, 35 €/mes)", j.o.values, 35.0), ("ORB US100 + cripto (futuros, 50 €/mes)", mix.values, 50.0),
                       ("ORB US100 solo en futuros (50 €/mes)", j.o.values, 50.0)]:
    sr = mm.mean() / mm.std() * np.sqrt(12)
    for perm in (None, "obj10"):
        out, al, rd = b.sim(mm, esc=0.45, perm=perm, cuota=cuota)
        print(f"{nom:42s} SR mensual {sr:4.2f} | permanente {perm or 'no':5s} | DARWIN/año {np.median(rd)*100:5.1f} % | "
              f"asignaciones 36 m {al.mean():4.1f} | neto €/año {out.mean()/3:7.0f} | mediana 36 m {np.median(out):7.0f} | P(neg) {(out<0).mean()*100:4.1f} %")
