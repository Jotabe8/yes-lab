import numpy as np, pandas as pd, sys
from motor import prep, correr, tday

def atr_diario(P):
    S=P['S']; h,l,c=P['h'],P['l'],P['c']
    H=np.array([h[a:b+1].max() for a,b in zip(S.a,S.b)]); L=np.array([l[a:b+1].min() for a,b in zip(S.a,S.b)])
    C=c[S.b.values]; pc=np.r_[np.nan,C[:-1]]
    tr=np.nanmax(np.c_[H-L,np.abs(H-pc),np.abs(L-pc)],axis=1)
    return H,L,pd.Series(tr).rolling(20).mean().shift(1).values

def f1(P):
    o,h,l,c,sp=P['o'],P['h'],P['l'],P['c'],P['sp']; S=P['S']
    H,L,_=atr_diario(P); rows=[]
    A=S.a.values; B=S.b.values
    for k in range(1,len(S)):
        a,b=A[k],B[k]
        if (S.index[k]-S.index[k-1]).days>4: continue
        pa,pb=B[k-1]+1,a-1
        lv={"prev":(H[k-1],L[k-1])}
        if pb-pa>=60: lv["pre"]=(h[pa:pb+1].max(),l[pa:pb+1].min())
        w1=min(a+119,b-1)
        for nm,(hi,lo) in lv.items():
            for side,lev in ((-1,hi),(1,lo)):
                if side==-1 and o[a]>=lev: continue
                if side==1 and o[a]<=lev: continue
                js=np.where(h[a:w1+1]>lev)[0] if side==-1 else np.where(l[a:w1+1]<lev)[0]
                if len(js)==0: continue
                j=a+js[0]; m=None
                for q in range(j,min(j+5,b-1)):
                    if (side==-1 and c[q]<lev) or (side==1 and c[q]>lev): m=q; break
                if m is None: continue
                i=m+1
                if side==-1: ext=h[j:m+1].max(); sd=(ext+2*sp[m])-o[i]
                else: ext=l[j:m+1].min(); sd=(o[i]+2*sp[i])-(ext-0) ; sd=o[i]+sp[i]-(ext-sp[m])
                if sd<=0 or sp[i]/sd>0.10: continue
                rows.append(dict(i=i,d=side,entp=o[i],stop_dist=sd,nivel=nm,send=b,day=S.index[k]))
    T=pd.DataFrame(rows); V={}
    for nm in ["prev","pre"]:
        t=T[T.nivel==nm]
        for ex,tpR,tm in [("1R",1.0,None),("2R",2.0,None),("30m",np.nan,30)]:
            x=t.copy(); x["tp_R"]=tpR; x["tmax"]=x.send if tm is None else x.i+tm-1
            V[f"F1_{nm}_{ex}"]=(x,True)
    return V

def f2(P):
    o,h,l,c,sp=P['o'],P['h'],P['l'],P['c'],P['sp']; S=P['S']; V={}
    for W in [1,5]:
        rows=[]
        for day,(a,b) in S.iterrows():
            r=c[a+W-1]-o[a]
            if r==0: continue
            i=a+W; dfade=-int(np.sign(r))
            if dfade==-1: sd=(h[a:a+W].max()+2*sp[a+W-1])-o[i]
            else: sd=o[i]+sp[i]-(l[a:a+W].min()-sp[a+W-1])
            if sd<=0 or sp[i]/sd>0.10: continue
            rows.append(dict(i=i,d=dfade,entp=o[i],stop_dist=sd,send=b,day=day))
        T=pd.DataFrame(rows)
        for H in [5,15]:
            x=T.copy(); x["tp_R"]=np.nan; x["tmax"]=x.i+H-1; V[f"F2_W{W}_H{H}"]=(x,True)
    return V

def f3(P,offset=0.0):
    o,h,l,c,sp=P['o'],P['h'],P['l'],P['c'],P['sp']; S=P['S']; _,_,A=atr_diario(P)
    step={"US100":100,"US30":100,"GER40":100,"US500":25}[P['sym']]; rows=[]
    for k,(day,(a,b)) in enumerate(S.iterrows()):
        At=A[k]
        if not np.isfinite(At): continue
        O=o[a]; sd=0.1*At
        ks=np.arange(np.floor((O-1.5*At)/step),np.ceil((O+1.5*At)/step)+1)
        for L in ks*step+offset*step:
            if abs(L-O)<0.2*At or abs(L-O)>1.5*At: continue
            side=-1 if L>O else 1
            js=np.where(h[a:b]>=L)[0] if side==-1 else np.where(l[a:b]<=L)[0]
            if len(js)==0: continue
            j=a+js[0]
            entp=max(L,o[j]) if side==-1 else min(L,o[j])
            if sp[j]/sd>0.10: continue
            rows.append(dict(i=j,d=side,entp=entp,stop_dist=sd,send=b,day=day))
    T=pd.DataFrame(rows); V={}
    for tpR in [1.0,2.0]:
        x=T.copy(); x["tp_R"]=tpR; x["tmax"]=np.minimum(x.i+60,x.send); V[f"F3_{int(tpR)}R"+("_desplazado" if offset else "")]=(x,False)
    return V
