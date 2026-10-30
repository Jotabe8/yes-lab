# Recalculo con las condiciones OFICIALES leídas en help.fundingpips.com y fundingpips.com (30/10/2026):
# - Precios 2-Step (diaria 5 %): Standard 72/195/349/652 $, Flex 64/175/299/555 $, Pro 55/145/249/466 $ (10/25/50/100K).
#   Halloween: -20 % clientes nuevos (-15 % existentes). Recompras: -15 % (cliente existente) en el escenario base.
# - Striking System solo con el ciclo "On Demand 100 %": con el quincenal 80 % no hay límite por idea.
# - Master: apalancamiento escalonado de índices (1:5 > 0,5 lotes) -> riesgo fondeado 0,75-1 %.
# - Standard: 8 %/5 %, 3 días, diaria 5 %, máx 10 %, 80 % quincenal, cuota devuelta en el 4º retiro.
# - Flex (95 %): 10 %/8 %, 3 días con >= 0,5 % por fase (se modela como 3 días mín.), diaria 4 %, máx 12 %,
#   95 % quincenal si hay >= 3 días con >= 0,5 % en el ciclo; sin devolución de cuota.
from fp_vs_ftmo import *
STD={10:72,25:195,50:349,100:652}; FLX={10:64,25:175,50:299,100:555}
e=lambda p,d:p*(1-d)/EUR
filas=[]
for esc,HC in (("base",0.05),("costes x2",0.10)):
    for k in (10,50,100):
        if k==10: r=resumen([cuenta("US100",10000,89,89,HC=HC)])
        else: r=resumen([cuenta("US100",k*1000,FTMO[k],FTMO[k],HC=HC)])
        r.update(esc=esc,caso=f"FTMO {k}K 2/1,5"); filas.append(r)
        for rf in (0.75,1.0):
            for q in (0.0,0.10):
                r=resumen([cuenta("US100",k*1000,e(STD[k],.2),e(STD[k],.15),rf=rf,t1=8,t2=5,mind=3,refund_n=4,q_news=q,HC=HC)])
                r.update(esc=esc,caso=f"FP Standard {k}K 2/{rf} noticias {int(q*100)} %"); filas.append(r)
                r=resumen([cuenta("US100",k*1000,e(FLX[k],.2),e(FLX[k],.15),rf=rf,t1=10,t2=8,mind=3,daily=4,maxdd=12,split=0.95,refund_n=99,q_news=q,HC=HC,minpos=3)])
                r.update(esc=esc,caso=f"FP Flex 95 {k}K 2/{rf} noticias {int(q*100)} %"); filas.append(r)
D=pd.DataFrame(filas)[["esc","caso","cuota_ini","media","mediana","p10","p_neg","caja_p10","cuotas"]]
pd.set_option("display.width",200); pd.set_option("display.float_format",lambda v:f"{v:,.0f}")
D.to_csv("fp_oficial.csv",index=False); print(D.to_string(index=False))
