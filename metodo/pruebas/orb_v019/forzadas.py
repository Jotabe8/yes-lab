import sys; sys.path.insert(0,"/home/user/yes-lab")
import pandas as pd, numpy as np
from metodo.comparar_ops import cargar_mt5, comparar
from metodo.pruebas.orb_v019.replica import simular
P="/mnt/user-data/uploads/Prop Firm Challenges/"
v=pd.read_pickle("/tmp/claude-0/v.pkl")
mt=pd.read_csv(P+"ea_v019/v019_test_tope21.csv",sep=";"); print(mt.RiesgoPct.value_counts())
mt["d"]=pd.to_datetime(mt.Fecha,format="%Y.%m.%d")
fond=set(mt.loc[mt.RiesgoPct.isin([1.5,0.375]),"d"])
py=simular(v, tope_pausa=21, be_fondeada=fond, desde="2022-01-01")
py.to_pickle("/tmp/claude-0/py_tope.pkl")
f=py[py.forzada]; print("Forzadas Python:"); print(f[["fecha","lado","r","pct"]].to_string())
print("Forzadas MT5 (riesgo reducido):"); print(mt[mt.RiesgoPct<0.5][["Fecha","Hora","Lado","RiesgoPct","R"]].to_string())
# pausas
for nom,dd in (("py",py.fecha),("mt5",mt.d)):
    g=dd.sort_values().diff().dt.days; print(nom,"pausa máx",g.max(),"pausas>30:",(g>30).sum(), "ops",len(dd))
