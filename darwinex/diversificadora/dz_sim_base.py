# Darwinex Zero con el ORB US100 v018: Monte Carlo 36 meses (bloques de 3 meses de la serie real, gestión BE 2R).
# Supuestos verificados nov-2026: cuota 45 €/mes (420 €/año), comisión 15 % sobre beneficio del capital asignado con HWM trimestral,
# DarwinIA SILVER mínimo 30.000 € por mes con rating >= 75, dura 3 meses (se solapan), garantía 25.000 € x 3 meses si no hay
# DarwinIA en los 6 primeros meses; asignación permanente 100.000 € instantánea 1.795 € / con objetivo +10 % 535 €.
# Supuestos NO verificables (aproximados): rating >= 75 cuando la rentabilidad del DARWIN a 6 meses >= UMBRAL y el mes actual >= 0
# (el rating pesa 67 % la rentabilidad de 6 meses, 22 % la del mes, 11 % el DD); el motor de riesgo escala 1 R a ESC % del DARWIN.
import numpy as np, pandas as pd
s=pd.read_csv('../dos-orb/serie_v018_be.csv',parse_dates=['d']).set_index('d')
def meses(col,a,b,hc): return ((s.loc[a:b,col]-hc).resample('ME').sum()).values
def sim(mens,esc=0.45,umbral=6.0,alloc=30000,perm=None,N=20000,T=36,seed=1,cuota=35.0):
    rng=np.random.default_rng(seed); L=len(mens); out=np.zeros(N); allocs=np.zeros(N); ret_d=np.zeros(N)
    for i in range(N):
        st=rng.integers(0,L-3,T//3+1); m=np.concatenate([mens[k:k+3] for k in st])[:T]*esc/100
        quote=np.cumprod(1+m); act=[]; cash=-cuota*T; hwm=0.0; pnl=0.0; got=False; n_al=0
        pact=False; q0=1.0
        if perm=='inst': cash-=1795; pact=True
        if perm=='obj10': cash-=535
        for t in range(T):
            cap=sum(a for a,l in act)+(100000 if pact else 0)
            pnl+=cap*m[t]
            act=[(a,l-1) for a,l in act if l>1]
            if perm=='obj10' and not pact and quote[t]/q0>=1.10: pact=True
            r6=np.prod(1+m[max(0,t-5):t+1])-1
            if t>=3 and r6*100>=umbral and m[t]>=0: act.append((alloc,3)); got=True; n_al+=1
            if t==6 and not got: act.append((25000,3))
            if t%3==2:
                if pnl>hwm: cash+=0.15*(pnl-hwm); hwm=pnl
        out[i]=cash; allocs[i]=n_al; ret_d[i]=quote[-1]**(12/T)-1
    return out,allocs,ret_d
filas=[]
casos={'base 2018-26 BE2R coste 0,05R':meses('Rbe','2018','2026',0.05),
       'prudente: costes x2 (0,10R)':meses('Rbe','2018','2026',0.10),
       'pesimista: 2018-21 sin BE (R reto)':meses('R','2018','2021',0.05)}
for nom,mm in casos.items():
  for esc in (0.35,0.45,0.60):
    for perm in (None,'obj10','inst'):
      o,a,rd=sim(mm,esc=esc,perm=perm)
      filas.append(dict(escenario=nom,R_a_pct=esc,permanente=perm or 'no',DARWIN_anual_pct=np.median(rd)*100,
        asignaciones_36m=a.mean(),neto_36m_media=o.mean(),neto_anual=o.mean()/3,mediana_36m=np.median(o),p10=np.percentile(o,10),p90=np.percentile(o,90),
        p_neg=(o<0).mean()*100))
d=pd.DataFrame(filas); pd.set_option('display.width',250); pd.set_option('display.float_format',lambda v:f'{v:,.1f}')
print(d.to_string(index=False)); d.to_csv('dz_sim.csv',index=False)
# sensibilidad al umbral del rating
for u in (3,6,9,12):
  o,a,rd=sim(casos['base 2018-26 BE2R coste 0,05R'],umbral=u)
  print('umbral %d%%: asignaciones %.1f, neto 36m media %.0f mediana %.0f'%(u,a.mean(),o.mean(),np.median(o)))
