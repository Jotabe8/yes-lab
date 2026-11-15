# F2 con ticks GER40 FTMO: desvanecer los primeros 30 s de la apertura de Fráncfort (preregistro F2, variantes tick)
import pandas as pd, numpy as np
from motor import tday
f="/mnt/user-data/uploads/Prop Firm Challenges/analisis/scalping_v2/ger_ticks_apertura.tsv.gz"
d=pd.read_csv(f,sep="\t",header=None,usecols=[0,1,2,3],names=["d","t","bid","ask"])
d["ts"]=pd.to_datetime(d.d+" "+d.t,format="%Y.%m.%d %H:%M:%S.%f")
d=d.dropna().drop_duplicates().sort_values("ts")
ny=(d.ts-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous="NaT",nonexistent="NaT")
d["loc"]=ny.dt.tz_convert("Europe/Berlin").dt.tz_localize(None); d=d.dropna(subset=["loc"])
d["day"]=d["loc"].dt.normalize(); d["sec"]=(d["loc"]-d.day).dt.total_seconds()-9*3600
d=d[(d.sec>=-30)&(d.sec<=400)]
print("días con ticks en apertura:",d.day.nunique(),"spread mediano 09:00-09:01:",(d.ask-d.bid)[(d.sec>=0)&(d.sec<60)].median())
rows=[]
for day,g in d.groupby("day"):
    s=g.sec.values; b=g.bid.values; a=g.ask.values
    w=(s>=0)&(s<30)
    if w.sum()<5: continue
    iw=np.where(w)[0]; r=b[iw[-1]]-b[iw[0]]
    if r==0: continue
    after=np.where(s>=30)[0]
    if len(after)==0: continue
    e=after[0]; dr=-int(np.sign(r)); sp=a[e]-b[e]
    hi,lo=b[iw].max(),b[iw].min()
    for H in [120,300]:
        ex=np.where(s>=s[e]+H)[0]
        if len(ex)==0: continue
        x=ex[0]
        for mode in ["real","placebo"]:
            reps=1 if mode=="real" else 20
            for rp in range(reps):
                dd=dr if mode=="real" else (1 if np.random.default_rng(hash((day.value,rp))%2**32).random()<0.5 else -1)
                if dd==-1: stop_a=hi+2*sp; sd=stop_a-b[e]
                else: stop_b=lo-sp; sd=a[e]-stop_b
                if mode=="placebo":   # mismo riesgo, espejo
                    sd=(hi+2*sp-b[e]) if dr==-1 else (a[e]-(lo-sp))
                    stop_a=b[e]+sd; stop_b=a[e]-sd
                if sd<=0 or sp/sd>0.10: continue
                out={}
                for sm in [0,1,2]:
                    ent=(b[e]+sm*sp) if dd==1 else b[e]
                    seg=slice(e,x+1); bb=b[seg]; aa=b[seg]+sm*(a[seg]-b[seg])
                    if dd==1:
                        stp=stop_b - (sp if sm==0 else 0)
                        hit=np.where(bb<=stp)[0]; px=bb[hit[0]] if len(hit) else bb[-1]; R=(px-ent)/sd
                    else:
                        hit=np.where(aa>=stop_a)[0]; px=aa[hit[0]] if len(hit) else aa[-1]; R=(ent-px)/sd
                    out[sm]=R
                rows.append(dict(day=day,H=H,mode=mode,rep=rp,bruto=out[0],neto=out[1],neto2=out[2]))
T=pd.DataFrame(rows); cut=pd.Timestamp("2024-01-01")
for H in [120,300]:
    for per,m in [("ajuste",T.day<cut),("prueba",T.day>=cut)]:
        x=T[(T.H==H)&m&(T["mode"]=="real")]; p=T[(T.H==H)&m&(T["mode"]=="placebo")]
        p95=np.percentile(p.groupby("rep").neto.mean(),95)
        yrs=(x.day.max()-x.day.min()).days/365.25
        print(f"F2tick_30s_H{H//60}m {per}: ops/año {len(x)/yrs:.0f} bruto {x.bruto.mean():+.3f} neto {x.neto.mean():+.3f} x2 {x.neto2.mean():+.3f} "
              f"t_neto {tday(x.neto.values,x.day.values):+.2f} t_bruto {tday(x.bruto.values,x.day.values):+.2f} placebo_p95 {p95:+.3f}")
