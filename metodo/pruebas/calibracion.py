# Calibración del embudo con casos conocidos. Uso: PYTHONPATH=. python metodo/pruebas/calibracion.py
# (necesita serie_v018_be.csv de los archivos del proyecto y ema20_trades.csv del PC de Jorge)
import pandas as pd
from metodo.embudo import embudo
D="/mnt/user-data/uploads/Prop Firm Challenges/cartera"
orb = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv")
for c in (0.02, 0.05):
    o = pd.DataFrame({"fecha": pd.to_datetime(orb.d), "r_bruto": orb.R + c - 0.02, "coste_r": c})
    print(f"== ORB US100 v018, coste {c} R, 50 pruebas"); print(embudo(o, 50, "2023-01-01")); print()
g = pd.read_csv(f"{D}/ger40_ema20/ema20_trades.csv")
e = pd.DataFrame({"fecha": pd.to_datetime(g.d), "r_bruto": g.Rgross, "coste_r": g.Rgross - g.R})
print("== GER40 EMA20, 105 pruebas"); print(embudo(e, 105, "2023-01-01"))
