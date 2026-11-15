import numpy as np, pandas as pd, sys
from motor import prep, correr, tday
from familias import atr_diario
from evaluar import resumen, CORTE

def ventana(P):
    return (630,930) if P['sym']!="GER40" else (600,990)   # minutos locales

def t1(P):
    o,h,l,c,sp,hm=P['o'],P['h'],P['l'],P['c'],P['sp'],P['hm']; S=P['S']; _,_,A=atr_diario(P)
    w0,w1=ventana(P); rows=[]
    for k,(day,(a,b)) in enumerate(S.iterrows()):
        At=A[k]
        if not np.isfinite(At): continue
        O=o[a]; n=(b-a+1)//5
        if n<20: continue
        idx=a+np.arange(n)*5
        bo=o[idx]; bc=c[idx+4]; bh=np.maximum.reduceat(h[a:a+n*5],np.arange(0,n*5,5)); bl=np.minimum.reduceat(l[a:a+n*5],np.arange(0,n*5,5))
        e=pd.Series(bc).ewm(span=20,adjust=False).mean().values
        for q in range(20,n-1):
            end=idx[q]+4; t=hm[end]
            if t<w0 or t>=w1: continue
            dist=bc[q]-O
            if abs(dist)<0.5*At: continue
            if dist>0 and bl[q]<=e[q] and bc[q]>e[q] and bc[q]>bo[q]: d=1
            elif dist<0 and bh[q]>=e[q] and bc[q]<e[q] and bc[q]<bo[q]: d=-1
            else: continue
            i=end+1; sd=0.15*At
            if sp[i]/sd>0.10: continue
            rows.append(dict(i=i,d=d,entp=o[i],stop_dist=sd,send=b,day=day)); break
    T=pd.DataFrame(rows); V={}
    for nm,tpR,tm in [("2R",2.0,None),("60m",np.nan,60)]:
        x=T.copy(); x["tp_R"]=tpR; x["tmax"]=x.send if tm is None else np.minimum(x.i+tm-1,x.send); V[f"T1_retroceso_{nm}"]=(x,True)
    return V

def t2(P):
    o,h,l,c,sp,hm=P['o'],P['h'],P['l'],P['c'],P['sp'],P['hm']; S=P['S']; _,_,A=atr_diario(P)
    w0,w1=ventana(P); V={}
    for filt in ["tend","libre"]:
        rows=[]
        for k,(day,(a,b)) in enumerate(S.iterrows()):
            At=A[k]
            if not np.isfinite(At): continue
            O=o[a]
            for j in range(a+30,b-1):
                t=hm[j]
                if t<w0: continue
                if t>=w1: break
                hi=h[j-30:j].max(); lo=l[j-30:j].min()
                if hi-lo>0.12*At: continue
                if c[j]>hi: d=1
                elif c[j]<lo: d=-1
                else: continue
                if filt=="tend":
                    dist=c[j]-O
                    if abs(dist)<0.5*At or np.sign(dist)!=d: continue
                i=j+1
                sd=(o[i]+sp[i]-(lo-sp[j])) if d==1 else ((hi+2*sp[j])-o[i])
                if sd<=0 or sp[i]/sd>0.10: continue
                rows.append(dict(i=i,d=d,entp=o[i],stop_dist=sd,send=b,day=day)); break
        T=pd.DataFrame(rows)
        for nm,tpR,tm in [("2R",2.0,None),("60m",np.nan,60)]:
            x=T.copy(); x["tp_R"]=tpR; x["tmax"]=x.send if tm is None else np.minimum(x.i+tm-1,x.send); V[f"T2_micro_{filt}_{nm}"]=(x,True)
    return V

if __name__=="__main__":
    sym=sys.argv[1]; modo=sys.argv[2] if len(sys.argv)>2 else "real"
    P=prep(sym, shuffle_seed=(7 if modo=="paseo" else None))
    V={}; V.update(t1(P)); V.update(t2(P))
    # series diarias para la correlación con el ORB
    from motor import correr
    orb=pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv",parse_dates=["d"]).set_index("d").R
    out=resumen(P,V,placebo=(modo=="real"))
    for r in out:
        T,tpf=V[r["variante"]]; R=correr(P,T,1,tpf)
        s=pd.Series(R,index=pd.to_datetime(T.day.values)).groupby(level=0).sum()
        j=pd.concat([s,orb],axis=1).fillna(0); j=j[(j.index>="2018-01-23")&(j.index<=orb.index.max())]
        r["corr_ORB"]=j.corr().iloc[0,1]
    df=pd.DataFrame(out); df.to_csv(f"/home/user/sc/tend_{sym}_{modo}.csv",index=False)
    pd.set_option("display.width",250); print(df.round(3).to_string(index=False))
