# ORB US100 en Goat Funded Trader 2-Step frente a FTMO 2-Step 10K, 1 año (05/11/2026).
# Mismo método que fundingpips/fp_vs_ftmo.py (bloques de 20 días 2022-26, 20.000 MC, coste 0,05 R, recompra al quemar).
# GFT (fuentes secundarias, ver RESULTADOS.md): días mínimos = 3 días con >= +0,5 % del saldo inicial (fases y por ciclo
# de pago), retiro cada 14 días naturales (~10 hábiles) al 80 % menos 2 % de comisión, los 2 primeros retiros con tope
# del 6 % del saldo inicial (el exceso se pierde), tope de beneficio diario 3.000 $, Goat Guard (cierre a -2 % flotante,
# split a la mitad) -> riesgo fondeado <= 1 %, noticias: beneficio de una fracción q de días ganadores recortado.
from fp_vs_ftmo import *
def gft(size,fee1,fee_re,rc=2.0,rf=1.0,t1=8,t2=6,daily=4,maxdd=10,split=0.8*0.98,cada=10,q_news=0.05,HC=0.05,cap_first=6.0):
    R,RB=S["US100"]; has=np.isfinite(R[IDX]); r=np.where(has,R[IDX]-HC,0); rb=np.where(has,RB[IDX]-HC,0)
    rb=np.where((rb>0)&(U_NEWS<q_news),np.minimum(rb,1.0/rf),rb)          # tope 1 % del saldo en operaciones con noticia
    bal=np.zeros(N); stg=np.zeros(N,int); gd=np.zeros(N); since=np.zeros(N); nrw=np.zeros(N)
    cash=np.zeros((N,12)); cash[:,0]-=fee1; fees=np.ones(N); funded=np.zeros(N,bool)
    capd=3000/size*100
    for t in range(DAYS):
        m=min(t*12//DAYS,11); fund=stg==2; risk=np.where(fund,rf,rc)
        pnl=np.maximum(np.where(fund,rb[:,t],r[:,t])*risk,-1.5*risk); pnl=np.minimum(pnl,capd); bal+=pnl
        gd+=pnl>=0.5
        fail=(bal<=-maxdd)|(pnl<=-daily)
        p1=(stg==0)&~fail&(bal>=t1)&(gd>=3); p2=(stg==1)&~fail&(bal>=t2)&(gd>=3); funded|=p2
        since=np.where(fund,since+1,0)
        can=fund&~fail&(since>=cada)&(bal*size/100>=100)&(gd>=3)
        amt=np.where(nrw<2,np.minimum(bal,cap_first),bal)
        nrw+=can
        cash[:,m]+=np.where(can,amt/100*size*split/EUR,0)-np.where(fail,fee_re,0)
        fees+=fail; nrw=np.where(fail,0,nrw)
        stg=np.where(fail,0,np.where(p1,1,np.where(p2,2,stg)))
        rs=fail|p1|p2|can; bal=np.where(rs,0,bal); gd=np.where(rs,0,gd); since=np.where(can|fail,0,since)
    return dict(cash=cash,fees=fees,lostf=np.zeros(N),funded=funded,fee1=fee1)

if __name__=="__main__":
    pd.set_option("display.width",250); pd.set_option("display.float_format",lambda v:f"{v:,.0f}")
    filas=[]
    def add(esc,caso,o):
        r=resumen([o]); r.update(esc=esc,caso=caso); filas.append(r)
    GOAT={8:56,15:98,25:148,50:288,100:458}; STD={8:108,15:208,25:228,50:338,100:594}
    for esc,HC in (("base",0.05),("costes x2",0.10)):
        add(esc,"FTMO 10K 2/1,5",cuenta("US100",10000,89,89,HC=HC))
        add(esc,"FTMO 25K 2/1,5",cuenta("US100",25000,250,250,HC=HC))
        for k in (8,15,25):
            for d in (0.4,0.5):
                for rf in (0.75,1.0):
                    f=GOAT[k]*(1-d)/EUR
                    add(esc,f"GFT GOAT {k}K -{int(d*100)} % 2/{rf}",gft(k*1000,f,f,rf=rf,HC=HC))
            f=STD[k]*0.6/EUR
            add(esc,f"GFT Standard {k}K -40 % 2/1,0",gft(k*1000,f,f,t1=10,t2=5,daily=5,HC=HC))
    D=pd.DataFrame(filas)[["esc","caso","cuota_ini","media","mediana","p10","p_neg","caja_p10","p_fondear","cuotas"]]
    D.to_csv("gft_vs_ftmo.csv",index=False); print(D.to_string(index=False))
