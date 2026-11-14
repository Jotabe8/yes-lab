import sys; sys.path.insert(0,"/home/user/yes-lab")
import pandas as pd, numpy as np
from metodo.comparar_ops import comparar, cargar_mt5
from metodo.pruebas.orb_v019.replica import simular
P="/mnt/user-data/uploads/Prop Firm Challenges/"
v=pd.read_pickle("/tmp/claude-0/v.pkl")
lv=pd.read_csv("/mnt/project-files/operaciones-live/ops_live.csv",sep=";")
lv["d"]=pd.to_datetime(lv.Fecha,format="%Y.%m.%d")
live=pd.DataFrame({"hora":lv.d+pd.Timedelta("16:40:00"),"lado":lv.Lado,"r":lv.R,"salida":pd.to_datetime(lv.Fecha+" "+lv.Hora,format="%Y.%m.%d %H:%M")})
print("datos hasta", v.index.max())
for filt in (False,True):
    py=simular(v, filtro_vol=filt, desde="2026-10-13")
    py=py[py.fecha<="2026-10-29"]
    pyd=py.assign(hora=py.fecha+pd.Timedelta("16:40:00"))
    c=comparar(pyd, live[live.hora<="2026-10-29 23:00"], tolerancia="1min")
    print("==== réplica filtro_vol =",filt); print(c)
    m=c.pares.merge(py[["fecha","hora","r","salida","pct"]].rename(columns={"hora":"sal_py"}),left_on=c.pares.hora_py.dt.normalize(),right_on="fecha").merge(live[["hora","salida"]].rename(columns={"salida":"sal_live"}),left_on="hora_mt5",right_on="hora")
    print(m[["fecha","lado","r_py","r_mt5","sal_py","sal_live","pct"]].to_string())
mt=cargar_mt5(P+"ea_v019/v019_test_tope21.csv"); mt=mt[mt.hora>="2026-10-13"]
d=mt.hora.dt.normalize(); mt=mt.assign(salida=mt.hora,hora=d+pd.Timedelta("16:40:00"))
c=comparar(mt.drop(columns="salida"), live, tolerancia="1min"); print("==== tester v019 tope frente a real"); print(c)
print(mt.to_string())
