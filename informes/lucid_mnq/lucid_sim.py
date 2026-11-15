# LucidFlex 50K con el ORB en micros MNQ: 1 año de Monte Carlo (bloques de 20 días) con la réplica del port
# (ref_combinada.csv: R de futuros sin horquilla y stop en puntos de cada día). 14-11-2026.
# Reglas oficiales (support.lucidtrading.com, 14-11-2026): MLL 2.000 $ EOD trailing que se bloquea en +100 $ cuando el
# saldo de cierre supera +2.100 $; al pedir retiro el suelo pasa a +100 $; objetivo 3.000 $; consistencia 40 % (solo reto);
# retiro con 5 días >= 150 $, 50 % del beneficio hasta 2.000 $, mínimo 500 $, 90 %; 5 retiros y la cuenta pasa a Live
# (aquí: se da por terminada y se compra otra, como en donde-operar/sim_futuros_prop.py). DLL opcional y blanda: no actúa con 1 op/día.
# Contratos enteros: q = round(riesgo / (stop*2 $ + coste)), bajando uno si pasa de riesgo*(1+exceso). Sin tope por el suelo
# ni "cuenta agotada" (probado: recortar cerca del suelo baja la media 400-650 €; ver lucid_sim_salida.txt).
import numpy as np, pandas as pd, sys
EUR=1.12; TOPE=None; DAYS=252; BLOCK=20; PV=2.0
X=pd.read_csv("ref_combinada.csv",parse_dates=["d"]).set_index("d")
def carga(prudente):
    cal=pd.bdate_range("2018-01-23","2021-12-31") if prudente else pd.bdate_range("2022-01-03","2026-09-30")
    Y=X.reindex(cal); return Y.Rf_reto.values, Y.Rf_fond.values, Y.stop_pts.values
def simula(riesgo,modo="enteros",coste=2.0,exceso=25,fee=80,prudente=False,N=10000,seed=7,escala=1.0,tope=None,agotada=0.0):
    """modo: 'continuo' (riesgo exacto en $, como el modelo anterior) o 'enteros' (micros MNQ).
    escala: multiplica los puntos del stop (para ver el efecto del nivel del Nasdaq: 1 = el de cada día)."""
    R,RB,SP=carga(prudente); rng=np.random.default_rng(seed)
    st=rng.integers(0,len(R)-BLOCK,(N,DAYS//BLOCK+1)); I=(st[:,:,None]+np.arange(BLOCK)).reshape(N,-1)[:,:DAYS]
    has=np.isfinite(R[I]); r=np.where(has,R[I],0.); rb=np.where(has,RB[I],0.); sp=np.where(has,SP[I]*escala,1.)
    bal=np.zeros(N); hi=np.zeros(N); fl=np.full(N,-2000.); fund=np.zeros(N,bool); best=np.zeros(N)
    qd=np.zeros(N); cyc=np.zeros(N); npa=np.zeros(N)
    cash=np.zeros((N,12)); cash[:,0]-=fee/EUR; fees=np.full(N,float(fee)); npay=np.zeros(N); pasa=np.zeros(N); rreal=[]
    for t in range(DAYS):
        m=min(t*12//DAYS,11)
        pc=sp[:,t]*PV+coste
        room=bal-fl-100
        agot=has[:,t]&(room<agotada*riesgo)
        if modo=="continuo":
            q=np.full(N,riesgo/pc)
        else:
            q=np.round(riesgo/pc); q=np.where(q*pc>riesgo*(1+exceso/100),q-1,q)
            q=q if tope is None else np.minimum(q,np.floor(np.maximum(room,0)/(pc*tope)))
            cap=np.where(fund,np.where(bal<1000,20,np.where(bal<2000,30,40)),40); q=np.minimum(q,cap); q=np.maximum(q,0)
        q=np.where(has[:,t]&~agot,q,0)
        x=np.where(fund,rb[:,t],r[:,t])
        pnl=q*(x*sp[:,t]*PV-coste); pnl=np.maximum(pnl,-1.5*q*pc)
        if t<DAYS: rreal.append(np.where(q>0,q*pc/riesgo,np.nan))
        bal+=pnl
        fail=(bal<=fl)|agot
        hi=np.maximum(hi,bal); fl=np.maximum(fl,np.minimum(hi-2000,100))
        best=np.where(~fund,np.maximum(best,pnl),best)
        ok=~fund&~fail&(bal>=3000)&(best<=0.40*bal)
        qd=np.where(fund&(pnl>=150),qd+1,qd); cyc=np.where(fund,cyc+pnl,cyc)
        amt=np.minimum(2000,0.5*np.maximum(bal,0))
        can=fund&~fail&(qd>=5)&(cyc>0)&(amt>=500)
        cash[:,m]+=np.where(can,amt*0.9/EUR,0); npay+=can; npa+=can
        bal=np.where(can,bal-amt,bal); fl=np.where(can,np.maximum(fl,100),fl); qd=np.where(can,0,qd); cyc=np.where(can,0,cyc)
        retira=fund&(npa>=5); fail=fail|retira
        pasa+=ok
        cash[:,m]-=np.where(fail,fee/EUR,0); fees+=np.where(fail,fee,0)
        fund=np.where(fail,False,np.where(ok,True,fund))
        z=fail|ok
        bal=np.where(z,0,bal); hi=np.where(z,0,hi); fl=np.where(z,-2000,fl); best=np.where(z,0,best); qd=np.where(z,0,qd); cyc=np.where(z,0,cyc); npa=np.where(fail,0,npa)
    n=cash.sum(1); cum=np.cumsum(cash,1); rr=np.array(rreal)
    return dict(riesgo=riesgo,modo=modo,coste=coste,fee=fee,media=n.mean(),mediana=np.median(n),p10=np.percentile(n,10),p_neg=(n<0).mean()*100,
                caja_p10=np.percentile(cum.min(1),10),cuotas=fees.mean(),aprobados=pasa.mean(),retiros=npay.mean(),
                riesgo_real_medio=np.nanmean(rr),riesgo_real_p10=np.nanpercentile(rr,10),riesgo_real_p90=np.nanpercentile(rr,90))
if __name__=="__main__":
    pd.set_option("display.width",250); pd.set_option("display.float_format",lambda v:f"{v:,.2f}")
    filas=[]
    for esc,kw in (("base 2022-26",dict()),("costes x2",dict(coste=4.0)),("tipo 2018-21",dict(prudente=True)),("cuota 115 $",dict(fee=115))):
        for rsk in (300,350,400,450,500):
            for modo in ("continuo","enteros"):
                o=simula(rsk,modo,tope=TOPE,**kw); o["esc"]=esc; filas.append(o)
    D=pd.DataFrame(filas); D.to_csv("lucid_sim.csv",index=False)
    for esc in D.esc.unique():
        print("\n==",esc); print(D[D.esc==esc].drop(columns=["esc"]).to_string(index=False))
    # contratos típicos por año (riesgo 330)
    Y=X[X.Rf_reto.notna()].copy(); pc=Y.stop_pts*PV+2; q=np.round(330/pc); q=np.where(q*pc>330*1.25,q-1,q); Y["q"]=q; Y["riesgo_real"]=q*pc
    print("\nMicros con riesgo 330 $ por año (stop de cada día):"); print(Y.groupby(Y.index.year).agg(stop_pts=("stop_pts","median"),micros=("q","median"),riesgo_real=("riesgo_real","mean"),dias_0=("q",lambda v:(v<1).sum())).to_string())
