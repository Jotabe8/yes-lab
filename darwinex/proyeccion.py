# Proyección anual DZ: 3 escenarios x 3 configuraciones. Mismo MC que dz_combinado.py.
import numpy as np, pandas as pd
b={}; exec(open("dz_sim_base.py").read().split("filas=[]")[0].replace("../dos-orb/serie_v018_be.csv","/mnt/project-files/dos-orb/serie_v018_be.csv"), b)
s=b["s"]; c=pd.read_csv("cripto_cartera_diaria.csv",parse_dates=["fecha"]).set_index("fecha").R
def mm(co, ccost_extra, chalf):
    o=(s.Rbe-co)["2021-03":"2026-10"].resample("ME").sum()
    cc=c["2021-03":"2026-10"]; cc=cc-ccost_extra
    if chalf: cc=cc-cc.mean()/2
    cm=cc.resample("ME").sum(); j=pd.concat([o,cm],axis=1,keys=["o","c"],sort=True).fillna(0)
    mix=j.o+j.c*(j.o.std()/j.c.std()); mix=mix*(j.o.std()/mix.std()); return j.o.values, mix.values
esc={"base":(0.05,0,False),"prudente (costes x2)":(0.10,0.045,False),"pesimista (edges a la mitad)":(None,0,True)}
for n,(co,ce,h) in esc.items():
    if co is None:
        o,mix=mm(0.05,0,True); o=o-o.mean()/2
    else: o,mix=mm(co,ce,h)
    for cfg,ser,cuota in [("CFD ORB US100",o,35.0),("Futuros ORB US100+cripto",mix,50.0)]:
        for perm in (None,"obj10"):
            out,al,rd=b["sim"](ser,esc=0.45,perm=perm,cuota=cuota)
            print(f"{n:30s} {cfg:26s} perm {perm or 'no':5s} | DARWIN {np.median(rd)*100:5.1f} %/año | media {out.mean()/3:6.0f} €/año | mediana {np.median(out)/3:6.0f} | p10 3a {np.percentile(out,10):7.0f} | p90 3a {np.percentile(out,90):7.0f} | P(neg 3a) {(out<0).mean()*100:4.1f} %")
