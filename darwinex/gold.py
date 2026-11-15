# DarwinIA SILVER + GOLD a 36 meses. Reglas GOLD (help.darwinex.com/darwinia + resultados abril 2026):
# historial > 8 meses; rentabilidad 1 año > 20 % y rentabilidad/DD > 2,5; ranking SOLO por la rentabilidad del mes;
# abril 2026: 140 de 596 con asignación, 9,68 M€ (media ~69 k€), el último premiado ganó +1,63 % ese mes. 6 meses, 15 % con HWM trimestral.
# Mientras cumple GOLD no entra en SILVER (vuelve a SILVER al mes siguiente si deja de cumplir).
# SILVER aproximado como en dz_sim.py: rating >= 75 si rentabilidad 6 m >= 6 % y mes >= 0 → 30 k€ 3 meses.
import numpy as np, pandas as pd
b={}; exec(open("dz_sim_base.py").read().split("filas=[]")[0].replace("../dos-orb/serie_v018_be.csv","/mnt/project-files/dos-orb/serie_v018_be.csv"), b)
s=b["s"]; c=pd.read_csv("cripto_cartera_diaria.csv",parse_dates=["fecha"]).set_index("fecha").R
def series(co, ce):
    o=(s.Rbe-co)["2021-03":"2026-10"].resample("ME").sum(); cm=(c-ce)["2021-03":"2026-10"].resample("ME").sum()
    j=pd.concat([o,cm],axis=1,keys=["o","c"],sort=True).fillna(0)
    mix=j.o+j.c*(j.o.std()/j.c.std()); mix=mix*(j.o.std()/mix.std()); return j.o.values, mix.values
def sim(mens, cuota, perm, gold_ok=True, umbral_g=1.6, gold_amt=69000, esc=0.45, N=20000, T=36, seed=1):
    rng=np.random.default_rng(seed); L=len(mens); out=np.zeros(N); ng=np.zeros(N); ns=np.zeros(N)
    for i in range(N):
        st=rng.integers(0,L-3,T//3+1); m=np.concatenate([mens[k:k+3] for k in st])[:T]*esc/100
        eq=np.cumprod(1+m); act=[]; cash=-cuota*T; hwm=0.; pnl=0.; got=False; pact=False
        if perm=="obj10": cash-=535
        for t in range(T):
            cap=sum(a for a,l in act)+(100000 if pact else 0); pnl+=cap*m[t]
            act=[(a,l-1) for a,l in act if l>1]
            if perm=="obj10" and not pact and eq[t]>=1.10: pact=True
            en_gold=False
            if gold_ok and t>=8:
                w=eq[max(0,t-12):t+1]/ (eq[t-12] if t>=12 else 1.0); r1=w[-1]-1
                dd=(1-w/np.maximum.accumulate(w)).max()
                en_gold = r1>0.20 and r1/max(dd,1e-9)>2.5
            if en_gold:
                if m[t]*100>=umbral_g: act.append((gold_amt,6)); ng[i]+=1; got=True
            else:
                r6=np.prod(1+m[max(0,t-5):t+1])-1
                if t>=3 and r6*100>=6 and m[t]>=0: act.append((30000,3)); got=True; ns[i]+=1
            if t==6 and not got: act.append((25000,3))
            if t%3==2 and pnl>hwm: cash+=0.15*(pnl-hwm); hwm=pnl
        out[i]=cash
    return out, ng.mean(), ns.mean()
filas=[]
for esc_nom,(co,ce) in {"base":(0.05,0),"prudente (costes x2)":(0.10,0.045)}.items():
    o,mix=series(co,ce)
    for cfg,ser,cuota in [("CFD ORB US100",o,35.0),("Futuros ORB US100+cripto",mix,50.0)]:
        for perm in (None,"obj10"):
            for g,ug,ga in [(False,0,0),(True,1.6,69000),(True,3.0,50000),(True,1.6,150000)]:
                out,ng,ns=sim(ser,cuota,perm,g,ug,ga)
                filas.append(dict(escenario=esc_nom,cuenta=cfg,permanente=perm or "no",
                    gold="no" if not g else f"mes>={ug}% {ga//1000}k",asig_gold_36m=ng,asig_silver_36m=ns,
                    media_anual=out.mean()/3,mediana_anual=np.median(out)/3,p10_36m=np.percentile(out,10),p_neg=(out<0).mean()*100))
d=pd.DataFrame(filas); pd.set_option("display.width",250); pd.set_option("display.float_format",lambda v:f"{v:,.1f}")
print(d.to_string(index=False)); d.to_csv("gold.csv",index=False)
