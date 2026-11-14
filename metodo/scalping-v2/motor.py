import numpy as np, pandas as pd
from numba import njit
from carga import load, SES

@njit(cache=True)
def sim(o,h,l,c,sp,ent_i,dr,entp,stop,tp,tmax,send,sm,rk,tp_first_bar):
    # entp: precio de entrada en bid (el largo paga +spread*sm). stop/tp en bid para largos, en ask para cortos.
    n=len(ent_i); R=np.zeros(n)
    for k in range(n):
        j=ent_i[k]; d=dr[k]; j0=j
        ent=entp[k]+(sp[j]*sm if d==1 else 0.0)
        while True:
            a=sp[j]*sm if d==-1 else 0.0
            lo=l[j]+a; hi=h[j]+a; op=o[j]+a
            if d==1 and lo<=stop[k]:
                px=min(op,stop[k]) if j>j0 else stop[k]; R[k]=(px-ent)/rk[k]; break
            if d==-1 and hi>=stop[k]:
                px=max(op,stop[k]) if j>j0 else stop[k]; R[k]=(ent-px)/rk[k]; break
            if (not np.isnan(tp[k])) and (j>j0 or tp_first_bar):
                if d==1 and hi>=tp[k]: R[k]=((max(op,tp[k]) if j>j0 else tp[k])-ent)/rk[k]; break
                if d==-1 and lo<=tp[k]: R[k]=(ent-(min(op,tp[k]) if j>j0 else tp[k]))/rk[k]; break
            if j>=tmax[k] or j>=send[k]:
                R[k]=d*(c[j]+a-ent)/rk[k]; break
            j+=1
    return R

def correr(P,T,sm,tp_first_bar=True):
    """T: DataFrame con i (vela de entrada), d, entp, stop_dist, tp_R (nan = sin objetivo), tmax, send, day"""
    o,h,l,c,sp=P['o'],P['h'],P['l'],P['c'],P['sp']
    i=T.i.values.astype(np.int64); d=T.d.values.astype(np.int64)
    entp=T.entp.values.astype(float); sd=T.stop_dist.values.astype(float)
    ent1=entp+np.where(d==1,sp[i],0.0)          # entrada neta (para fijar el riesgo igual en todas las variantes)
    # stop y objetivo fijados respecto a la entrada neta; en ask para cortos
    stop=np.where(d==1,ent1-sd,ent1+sd)
    tpR=T.tp_R.values.astype(float)
    tp=np.where(np.isnan(tpR),np.nan,np.where(d==1,ent1+tpR*sd,ent1-tpR*sd))
    if sm==0:  # en bruto: todo en bid, sin spread: desplazar niveles al bid
        stop=np.where(d==1,stop-sp[i],stop); tp=np.where(d==1,tp-sp[i],tp)
        stop=np.where(d==-1,stop,stop); 
    R=sim(o,h,l,c,sp,i,d,entp,stop,tp,T.tmax.values.astype(np.int64),T.send.values.astype(np.int64),float(sm),sd,tp_first_bar)
    return R

def prep(sym, shuffle_seed=None):
    d=load(sym).copy()
    o,h,l,c,sp=(d[x].values.astype(float) for x in ["open","high","low","close","spread"])
    loc=d["loc"]; day=loc.dt.normalize().values; hm=(loc.dt.hour*60+loc.dt.minute).values
    if shuffle_seed is not None:   # paseo aleatorio: barajar velas dentro de cada día
        rng=np.random.default_rng(shuffle_seed)
        gap=np.r_[0,o[1:]-c[:-1]]; dh,dl,dc=h-o,l-o,c-o
        _,st=np.unique(day,return_index=True); st=list(st)+[len(d)]
        perm=np.arange(len(d))
        for a,b in zip(st[:-1],st[1:]):
            if b-a>2: perm[a+1:b]=a+1+rng.permutation(b-a-1)
        g2,dh2,dl2,dc2=gap[perm],dh[perm],dl[perm],dc[perm]
        o2=np.empty_like(o); c2=np.empty_like(c); o2[0]=o[0]; c2[0]=o2[0]+dc2[0]
        for i in range(1,len(d)):
            o2[i]=(o[i] if day[i]!=day[i-1] else c2[i-1]+g2[i]); c2[i]=o2[i]+dc2[i]
        h=o2+np.maximum(dh2,np.maximum(dc2,0)); l=o2+np.minimum(dl2,np.minimum(dc2,0)); o=o2; c=c2
    s0,s1=[int(x[:2])*60+int(x[3:]) for x in SES[sym]]
    ins=(hm>=s0)&(hm<s1)
    # sesiones: índices primer/último minuto de contado por día
    idx=np.where(ins)[0]
    ser=pd.Series(idx,index=day[idx]); first=ser.groupby(level=0).min(); last=ser.groupby(level=0).max()
    first_hm=hm[first.values]; ok=first_hm==s0
    S=pd.DataFrame({"a":first.values,"b":last.values},index=first.index)[ok]
    S=S[(S.b-S.a)>(s1-s0)*0.8]  # sesiones casi completas
    return dict(o=o,h=h,l=l,c=c,sp=sp,day=day,hm=hm,S=S,s0=s0,s1=s1,sym=sym)

def tday(R,days):
    x=pd.Series(R,index=days).groupby(level=0).sum()
    return x.mean()/x.std(ddof=1)*np.sqrt(len(x)) if len(x)>2 else np.nan
