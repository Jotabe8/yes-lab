# Cuentas pequeñas (presupuesto de Jorge): FTMO 2-Step 10K (89 €) frente a FundingPips 2-Step Standard 10K
# (63 $ de lista, -20 % la primera). En 10K no hay Striking System; el tope de riesgo fondeado depende del margen.
from fp_vs_ftmo import *
filas=[]
for esc,HC in (("base",0.05),("costes x2",0.10)):
    r=resumen([cuenta("US100",10000,89,89,HC=HC)]); r.update(esc=esc,caso="FTMO 10K US100 2/1,5"); filas.append(r)
    for rf in (0.75,1.0,1.5):
        for q in (0.0,0.10):
            r=resumen([cuenta("US100",10000,fp(10,0.2),fp(10),rf=rf,t1=8,t2=5,mind=3,refund_n=4,q_news=q,HC=HC)])
            r.update(esc=esc,caso=f"FP 10K US100 2/{rf} noticias {int(q*100)} %"); filas.append(r)
D=pd.DataFrame(filas)[["esc","caso","cuota_ini","media","mediana","p10","p_neg","caja_p10","cuotas"]]
pd.set_option("display.width",200); pd.set_option("display.float_format",lambda v:f"{v:,.0f}")
D.to_csv("fp_10k.csv",index=False); print(D.to_string(index=False))
