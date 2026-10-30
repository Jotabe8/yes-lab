# ORB US100 en FTMO Futures (MNQ), 1 año, Monte Carlo con bloques de 20 días (mismo método que dos-orb/).
# Reglas oficiales (ftmo.com/en/futures/trading-objectives-and-rules, 30/10/2026):
#  Growth 50/100/150K: 119/169/229 $/mes, objetivo 3/6/9K, pérdida máx. EOD trailing 2/3,5/5K que se bloquea en el saldo
#   inicial, sin diaria en el reto (blanda 1/2/3K en fondeada), consistencia 40 % (solo reto), retiro tras 4 días
#   >=150/250/300 $, 50 % del beneficio, tope 2,5/3/4K por retiro, 90 %.
#  Pro 50/100/150K: 139/199/269 $/mes, objetivo igual, pérdida máx. 3/4,5/6K, diaria DURA 1/1,5/2K, consistencia 50 %,
#   retiro tras 5 días >=200/300/500 $, hasta 100 % del beneficio, tope 5/6/8K.
#  Ambos: >=50 % de cada retiro debe ser beneficio del ciclo actual; la suscripción se cancela al aprobar;
#   el retiro baja el saldo pero el suelo no baja (si se retira todo con el suelo bloqueado, la cuenta muere).
# Riesgo por operación en $ = pérdida máx. / K. Coste por operación en R (MNQ: comisión FTMO 0,20 $/lado +
#   CME ~0,35 $/lado + NFA 0,02 + 1 tick de deslizamiento ~ 2 $ ida y vuelta frente a ~115 $ de riesgo por MNQ).
# Al quemar el reto: reset inmediato (cuota de reset) o esperar al siguiente cobro mensual.
import numpy as np, pandas as pd
EUR=1.12; DAYS=252; BLOCK=20; MES=21
PLANES={
 "Growth 50K": dict(fee=119,reset=109,tgt=3000,dd=2000,dll_e=None,dll_f=None,cons=.40,qd=4,qmin=150,frac=.5,cap=2500),
 "Growth 100K":dict(fee=169,reset=159,tgt=6000,dd=3500,dll_e=None,dll_f=None,cons=.40,qd=4,qmin=250,frac=.5,cap=3000),
 "Growth 150K":dict(fee=229,reset=219,tgt=9000,dd=5000,dll_e=None,dll_f=None,cons=.40,qd=4,qmin=300,frac=.5,cap=4000),
 "Pro 50K":    dict(fee=139,reset=129,tgt=3000,dd=3000,dll_e=1000,dll_f=1000,cons=.50,qd=5,qmin=200,frac=1.,cap=5000),
 "Pro 100K":   dict(fee=199,reset=189,tgt=6000,dd=4500,dll_e=1500,dll_f=1500,cons=.50,qd=5,qmin=300,frac=1.,cap=6000),
 "Pro 150K":   dict(fee=269,reset=259,tgt=9000,dd=6000,dll_e=2000,dll_f=2000,cons=.50,qd=5,qmin=500,frac=1.,cap=8000),
}
def carga(prudente):
    t=pd.read_csv("serie_v018_be.csv",parse_dates=["d"]).set_index("d").sort_index(); t=t[~t.index.duplicated()]
    cal=pd.bdate_range("2018-01-23","2021-12-31") if prudente else pd.bdate_range("2022-01-19","2026-10-23")
    return t.R.reindex(cal).values,t.Rbe.reindex(cal).values
def simula(plan,K=5,HC=0.03,colchon=0.0,frac=None,reset=True,prudente=False,N=20000,seed=7):
    """colchón: tras el retiro el saldo debe quedar >= suelo + colchón*riesgo (en R). frac: fracción del beneficio a retirar."""
    p=PLANES[plan]; fr=p["frac"] if frac is None else min(frac,p["frac"])
    R,RB=carga(prudente); rng=np.random.default_rng(seed)
    st=rng.integers(0,len(R)-BLOCK,(N,DAYS//BLOCK+1)); I=(st[:,:,None]+np.arange(BLOCK)).reshape(N,-1)[:,:DAYS]
    has=np.isfinite(R[I]); r=np.where(has,R[I]-HC,0.); rb=np.where(has,RB[I]-HC,0.)
    risk=p["dd"]/K; dd=p["dd"]
    bal=np.zeros(N); hi=np.zeros(N); fl=np.full(N,-dd); fund=np.zeros(N,bool); best=np.zeros(N)
    qd=np.zeros(N); cyc=np.zeros(N); wait=np.zeros(N,bool); bill=np.zeros(N)
    cash=np.zeros((N,12)); cash[:,0]-=p["fee"]; fees=np.full(N,float(p["fee"])); npay=np.zeros(N); pasa=np.zeros(N); pierde_f=np.zeros(N)
    for t in range(DAYS):
        m=min(t*12//DAYS,11)
        ev=~fund
        # cobro mensual mientras siga en reto
        cobro=ev&(t-bill>=MES)&(t>0); cash[:,m]-=np.where(cobro,p["fee"],0); fees+=np.where(cobro,p["fee"],0); bill=np.where(cobro,t,bill)
        wait=wait&~cobro  # tras quemar sin reset, el nuevo reto llega con el cobro
        act=~wait
        pnl=np.where(act,np.where(fund,rb[:,t],r[:,t])*risk,0.); pnl=np.maximum(pnl,-1.5*risk)
        bal+=pnl
        dll=np.where(fund,p["dll_f"] or 1e18,p["dll_e"] or 1e18)
        fail=act&((bal<=fl)|(pnl<=-dll))
        # fin de día: suelo EOD trailing que se bloquea en el saldo inicial (0)
        hi=np.maximum(hi,bal); fl=np.maximum(fl,np.minimum(hi-dd,0))
        best=np.where(ev,np.maximum(best,pnl),best)
        ok=ev&act&~fail&(bal>=p["tgt"])&(best<=p["cons"]*bal)
        # fondeada: días que cuentan y retiro
        qd=np.where(fund&(pnl>=p["qmin"]),qd+1,qd); cyc=np.where(fund,cyc+pnl,cyc)
        lim=bal-(fl+colchon*risk)            # lo que se puede retirar sin dejar el saldo pegado al suelo
        amt=np.minimum.reduce([np.full(N,p["cap"]),fr*np.maximum(bal,0),2*np.maximum(cyc,0),np.maximum(lim,0)])
        can=fund&~fail&(qd>=p["qd"])&(amt>=20)
        cash[:,m]+=np.where(can,amt*0.9/EUR,0); npay+=can
        bal=np.where(can,bal-amt,bal); qd=np.where(can,0,qd); cyc=np.where(can,0,cyc)
        # fallo y aprobación
        pierde_f+=fail&fund; pasa+=ok
        ffail=fail&ev
        if reset:
            cash[:,m]-=np.where(ffail,p["reset"],0); fees+=np.where(ffail,p["reset"],0)
        else:
            wait|=ffail
        # fondeada perdida: nueva suscripción
        nf=fail&fund; cash[:,m]-=np.where(nf,p["fee"],0); fees+=np.where(nf,p["fee"],0); bill=np.where(nf,t,bill)
        fund=np.where(fail,False,np.where(ok,True,fund))
        z=fail|ok
        bal=np.where(z,0,bal); hi=np.where(z,0,hi); fl=np.where(z,-dd,fl); best=np.where(z,0,best); qd=np.where(z,0,qd); cyc=np.where(z,0,cyc)
    n=cash.sum(1); cum=np.cumsum(cash,1); pc=np.percentile
    return dict(plan=plan,K=K,riesgo_usd=risk,colchon=colchon,frac=fr,media=n.mean(),mediana=np.median(n),p10=pc(n,10),p90=pc(n,90),
                p_neg=(n<0).mean()*100,caja_p10=pc(cum.min(1),10),cuotas_eur=fees.mean()/EUR,retiros=npay.mean(),
                aprobados=pasa.mean(),fondeadas_perdidas=pierde_f.mean())
if __name__=="__main__":
    pd.set_option("display.width",250); pd.set_option("display.max_columns",30); pd.set_option("display.float_format",lambda v:f"{v:,.1f}")
    filas=[]
    for esc,kw in (("base",dict(HC=0.03)),("costes x2",dict(HC=0.06)),("US100 tipo 2018-21",dict(HC=0.03,prudente=True))):
        for plan in PLANES:
            for K in (4,5,6,8,10):
                for col in ((0,1,2) if plan.startswith("Pro") else (0,)):
                    o=simula(plan,K=K,colchon=col,**kw); o["esc"]=esc; filas.append(o)
        print(esc,flush=True)
    D=pd.DataFrame(filas); D.to_csv("futuros_ftmo.csv",index=False)
    for esc in D.esc.unique():
        d=D[D.esc==esc]; print("\n==",esc); print(d.sort_values("media",ascending=False).groupby("plan").head(3).drop(columns="esc").to_string(index=False))
