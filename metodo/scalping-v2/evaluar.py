import numpy as np, pandas as pd, sys
from motor import prep, correr, tday
from familias import f1,f2,f3
CORTE={"US100":("2023-01-01",2018),"US30":("2023-01-01",2018),"US500":("2023-01-01",2018),"GER40":("2024-01-01",2021.9)}
def resumen(P,V,placebo=True,seed=0):
    out=[]; sym=P['sym']; cut=pd.Timestamp(CORTE[sym][0])
    for name,(T,tpf) in V.items():
        if len(T)==0: continue
        R0=correr(P,T,0,tpf); R1=correr(P,T,1,tpf); R2=correr(P,T,2,tpf)
        pl=[]
        if placebo:
            rng=np.random.default_rng(seed)
            for r in range(20):
                X=T.copy(); X["d"]=rng.choice([-1,1],len(X)); pl.append(correr(P,X,1,tpf))
        days=pd.to_datetime(T.day.values)
        for per,m in [("ajuste",days<cut),("prueba",days>=cut)]:
            if m.sum()<10: continue
            yrs=(days[m].max()-days[m].min()).days/365.25
            row=dict(mercado=sym,variante=name,periodo=per,ops_anio=m.sum()/yrs,bruto=np.nanmean(R0[m]),neto=np.nanmean(R1[m]),
                     neto_x2=np.nanmean(R2[m]),coste_R=np.nanmean(R0[m]-R1[m]),t_neto=tday(R1[m],days[m]),t_bruto=tday(R0[m],days[m]))
            if placebo: row["placebo_p95"]=np.percentile([np.nanmean(p[m]) for p in pl],95)
            out.append(row)
    return out
if __name__=="__main__":
    sym=sys.argv[1]; modo=sys.argv[2] if len(sys.argv)>2 else "real"
    P=prep(sym, shuffle_seed=(7 if modo=="paseo" else None))
    V={}; V.update(f1(P)); V.update(f2(P)); V.update(f3(P)); V.update(f3(P,0.37))
    df=pd.DataFrame(resumen(P,V,placebo=(modo=="real")))
    df.to_csv(f"/home/user/sc/res_{sym}_{modo}.csv",index=False)
    pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
    print(df.round(3).to_string(index=False))
