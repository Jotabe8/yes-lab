# ORB US100 y GER40 en FundingPips 2-Step Standard (y 2-Step Pro) frente a FTMO 2-Step, 1 año (30/10/2026).
# Mismo método que dos-orb/dos_orb.py: bloques de 20 días hábiles 2022-26, mismas fechas para todos los casos,
# coste 0,05 R (x2 = 0,10), pérdida por operación acotada a 1,5 R, recompra inmediata al quemar, retiro cada 10 días.
# FundingPips: objetivos 8 % / 5 %, 3 días mín., diaria 5 %, máx. 10 % estática; en fondeada (Master) el riesgo se
# limita por el apalancamiento escalonado de índices (1:5 por encima de 0,5 lotes) y el Striking System (aviso con
# flotante -1,2 % por idea en cuentas >= 25K): se modela con riesgo fondeado 0,75 % o 1 %.
# Noticias (solo Master): se quita el beneficio de una fracción q de los días ganadores (operación abierta/cerrada
# a menos de 5 min de una noticia fuerte). Cuota devuelta en el 4º retiro (FTMO: en el 1º).
import numpy as np, pandas as pd
EUR=1.12
def carga(f):
    t=pd.read_csv(f,parse_dates=["d"]).set_index("d").sort_index(); return t[~t.index.duplicated()]
US=carga("serie_v018_be.csv"); GE=carga("serie_ger40.csv")
cal=pd.bdate_range("2022-01-19","2026-10-23")
S={"US100":(US.R.reindex(cal).values,US.Rbe.reindex(cal).values),"GER40":(GE.R.reindex(cal).values,GE.Rbe.reindex(cal).values)}
N=20000; DAYS=252; BLOCK=20
rng=np.random.default_rng(7)
st=rng.integers(0,len(cal)-BLOCK,(N,DAYS//BLOCK+1)); IDX=(st[:,:,None]+np.arange(BLOCK)).reshape(N,-1)[:,:DAYS]
U_NEWS=np.random.default_rng(11).random((N,DAYS))

def cuenta(name,size,fee1,fee_re,rc=2.0,rf=1.5,t1=10,t2=5,mind=4,daily=5,maxdd=10,split=0.8,cada=10,
           refund_n=1,q_news=0.0,HC=0.05,mensual=False,minpos=0):
    """fee1/fee_re en €: primera compra y recompras. mensual=True: ciclo de 21 días al 100 % con condiciones FP
    (>= 7 días con >= 0,5 %, mejor día <= 35 % del beneficio del ciclo); si no se cumplen, el ciclo sigue."""
    R,RB=S[name]; has=np.isfinite(R[IDX]); r=np.where(has,R[IDX]-HC,0); rb=np.where(has,RB[IDX]-HC,0)
    rb=np.where((rb>0)&(U_NEWS<q_news),0,rb)  # beneficio anulado por la regla de noticias (solo se usa en fondeada)
    bal=np.zeros(N); stg=np.zeros(N,int); td=np.zeros(N); since=np.zeros(N); nrw=np.zeros(N)
    gd=np.zeros(N); best=np.zeros(N)
    cash=np.zeros((N,12)); cash[:,0]-=fee1; fees=np.ones(N); paid=np.full(N,fee1); lostf=np.zeros(N); funded=np.zeros(N,bool)
    USD=size
    for t in range(DAYS):
        m=min(t*12//DAYS,11); fund=stg==2
        risk=np.where(fund,rf,rc)
        pnl=np.maximum(np.where(fund,rb[:,t],r[:,t])*risk,-1.5*risk); bal+=pnl; td+=has[:,t]
        fail=(bal<=-maxdd)|(pnl<=-daily); lostf+=fail&fund
        p1=(stg==0)&~fail&(bal>=t1)&(td>=mind); p2=(stg==1)&~fail&(bal>=t2)&(td>=mind); funded|=p2
        since=np.where(fund,since+1,0)
        gd=np.where(fund,gd+(pnl>=0.5),0); best=np.where(fund,np.maximum(best,pnl),0)
        if mensual:
            can=fund&~fail&(since>=21)&(bal>=1)&(gd>=7)&(best<=0.35*bal); sp=1.0
        else:
            can=fund&~fail&(since>=cada)&(bal>=1)&(gd>=minpos); sp=split
        nrw+=can
        ref=can&(nrw==refund_n)
        cash[:,m]+=np.where(can,bal/100*USD*sp/EUR,0)+np.where(ref,paid,0)-np.where(fail,fee_re,0)
        since=np.where(can,0,since); gd=np.where(can,0,gd); best=np.where(can,0,best)
        fees+=fail; paid=np.where(fail,fee_re,paid); nrw=np.where(fail,0,nrw)
        stg=np.where(fail,0,np.where(p1,1,np.where(p2,2,stg)))
        rs=fail|p1|p2|can; bal=np.where(rs,0,bal); td=np.where(fail|p1|p2,0,td)
    return dict(cash=cash,fees=fees,lostf=lostf,funded=funded,fee1=fee1)

def resumen(partes):
    cash=sum(o["cash"] for o in partes); n=cash.sum(1); cum=np.cumsum(cash,1); pc=np.percentile
    return dict(cuota_ini=sum(o["fee1"] for o in partes),media=n.mean(),mediana=np.median(n),p10=pc(n,10),
                p_neg=(n<0).mean()*100,caja_p10=pc(np.minimum(cum.min(1),0),10),
                p_fondear=np.mean([o["funded"].mean() for o in partes])*100,cuotas=sum(o["fees"].mean() for o in partes))

# precios: FTMO en € (web); FundingPips 2-Step Standard en $ de lista (cryptoslate ago-2026) -> €; Halloween -20 % nuevos
FTMO={25:250,50:345,100:540}
FPL={10:63,25:168,50:285,100:544}; FPPRO={10:55,25:134,50:224,100:422}
fp=lambda k,d=0.0:FPL[k]*(1-d)/EUR

if __name__=="__main__":
    pd.set_option("display.width",250); pd.set_option("display.float_format",lambda v:f"{v:,.0f}")
    filas=[]
    def add(esc,firma,caso,partes): r=resumen(partes); r.update(esc=esc,firma=firma,caso=caso); filas.append(r)
    for esc,HC in (("base",0.05),("costes x2",0.10)):
        for k in (50,100):
            add(esc,"FTMO 2-Step",f"US {k}K 2/1,5",[cuenta("US100",k*1000,FTMO[k],FTMO[k],HC=HC)])
            for rf in (0.75,1.0):
                for q in (0.0,0.10):
                    add(esc,"FP 2-Step Std",f"US {k}K 2/{rf} noticias {int(q*100)} %",
                        [cuenta("US100",k*1000,fp(k,0.2),fp(k),rf=rf,t1=8,t2=5,mind=3,refund_n=4,q_news=q,HC=HC)])
            add(esc,"FP 2-Step Std",f"US {k}K 2/0,75 mensual 100 %",
                [cuenta("US100",k*1000,fp(k,0.2),fp(k),rf=0.75,t1=8,t2=5,mind=3,refund_n=4,q_news=0.10,HC=HC,mensual=True)])
            # 2-Step Pro: 6 %/6 %, diaria 3 %, máx 6 %, 1 día mín., 80 % semanal (cada 5 días), sin devolución, sin Striking
            add(esc,"FP 2-Step Pro",f"US {k}K 1/0,75",
                [cuenta("US100",k*1000,FPPRO[k]*0.8/EUR,FPPRO[k]/EUR,rc=1.0,rf=0.75,t1=6,t2=6,mind=1,daily=3,maxdd=6,cada=5,refund_n=99,q_news=0.10,HC=HC)])
        # combinación recomendada en FTMO y su equivalente en FP
        add(esc,"FTMO 2-Step","US 100K + GER 50K",[cuenta("US100",100000,540,540,HC=HC),cuenta("GER40",50000,345,345,HC=HC)])
        add(esc,"FP 2-Step Std","US 100K + GER 50K (2/0,75, noticias 10 %)",
            [cuenta("US100",100000,fp(100,0.2),fp(100),rf=0.75,t1=8,t2=5,mind=3,refund_n=4,q_news=0.10,HC=HC),
             cuenta("GER40",50000,fp(50,0.2),fp(50),rf=0.75,t1=8,t2=5,mind=3,refund_n=4,q_news=0.10,HC=HC)])
        add(esc,"FTMO 2-Step","US 50K + GER 25K",[cuenta("US100",50000,345,345,HC=HC),cuenta("GER40",25000,250,250,HC=HC)])
        add(esc,"FP 2-Step Std","US 50K + GER 25K (2/0,75, noticias 10 %)",
            [cuenta("US100",50000,fp(50,0.2),fp(50),rf=0.75,t1=8,t2=5,mind=3,refund_n=4,q_news=0.10,HC=HC),
             cuenta("GER40",25000,fp(25,0.2),fp(25),rf=0.75,t1=8,t2=5,mind=3,refund_n=4,q_news=0.10,HC=HC)])
        # control: FP con riesgo fondeado 1,5 % como FTMO (no viable por margen/Striking; para aislar el efecto)
        add(esc,"FP (control irreal)","US 100K 2/1,5 sin noticias",[cuenta("US100",100000,fp(100,0.2),fp(100),t1=8,t2=5,mind=3,refund_n=4,HC=HC)])
    D=pd.DataFrame(filas)[["esc","firma","caso","cuota_ini","media","mediana","p10","p_neg","caja_p10","p_fondear","cuotas"]]
    D.to_csv("fp_vs_ftmo.csv",index=False); print(D.to_string(index=False))
