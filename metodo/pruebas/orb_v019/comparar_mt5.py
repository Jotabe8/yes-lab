import sys; sys.path.insert(0,"/home/user/yes-lab")
import pandas as pd, numpy as np
from metodo.comparar_ops import cargar_mt5, comparar
P="/mnt/user-data/uploads/Prop Firm Challenges/"
py=pd.read_pickle("sys.argv[2]")
def por_dia_mt5(path):
    mt=cargar_mt5(path)
    d=mt.hora.dt.normalize()
    d=d.where(mt.hora.dt.hour*60+mt.hora.dt.minute>=16*60+40, d-pd.offsets.BDay(1))
    return mt.assign(salida=mt.hora, hora=d+pd.Timedelta("16:40:00"))
pyd=py.assign(hora=py.fecha+pd.Timedelta("16:40:00"))
for nom in ["v018_test_base","v019_test_tope21"]:
    mt=por_dia_mt5(P+f"ea_v019/{nom}.csv")
    c=comparar(pyd,mt,tolerancia="1min")
    print("=====",nom); print(c)
    m=c.pares.merge(mt[["hora","salida"]],left_on="hora_mt5",right_on="hora").merge(py[["fecha","hora","salida","r"]].rename(columns={"hora":"sal_py","salida":"tipo_py"}),left_on=c.pares.hora_py.dt.normalize(),right_on="fecha")
    big=m[m.dr.abs()>0.1]
    print("pares |dR|>0.1:",len(big)); print(big[["fecha","lado","r_py","r_mt5","sal_py","salida","tipo_py"]].to_string())
