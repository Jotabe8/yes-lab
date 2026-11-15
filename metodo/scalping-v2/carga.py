import pandas as pd, numpy as np, os
D="/mnt/user-data/uploads/Prop Firm Challenges/data"
def _rd(f,fsp):
    d=pd.read_csv(f"{D}/{f}",usecols=["time","open","high","low","close","spread"])
    d["time"]=pd.to_datetime(d.time); d["spread"]=d.spread*fsp; return d
def load(sym):
    c=f"/home/user/sc/{sym}.pkl"
    if os.path.exists(c): return pd.read_pickle(c)
    if sym=="US100":
        a=_rd("US100_M1_DUKA_2018_2022.csv",0.01); a=a[a.time<"2023-01-01"]
        b=_rd("US100_cash_M1_FTMO.csv",0.01); b=b[b.time>="2023-01-01"]
        e=_rd("US100_cash_M1_FTMO_hasta_nov.csv",0.01)
        d=pd.concat([a,b,e])
    elif sym=="GER40": d=_rd("GER40_M1_FTMO.csv",1.0); d=d[d.time>="2021-11-22"]
    elif sym=="US30": d=_rd("USA30IDXUSD_M1_DUKA.csv",1.0)
    elif sym=="US500": d=_rd("USA500IDXUSD_M1_DUKA.csv",1.0)
    d=d.sort_values("time").drop_duplicates("time",keep="last")
    d=d[d.time>="2018-01-01"].reset_index(drop=True)
    # hora local de la bolsa: servidor = NY+7
    ny=(d.time-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous="NaT",nonexistent="NaT")
    if sym=="GER40": loc=ny.dt.tz_convert("Europe/Berlin")
    else: loc=ny
    d["loc"]=loc.dt.tz_localize(None)
    d=d.dropna(subset=["loc"]).reset_index(drop=True)
    d.to_pickle(c); return d
SES={"US100":("09:30","16:00"),"US30":("09:30","16:00"),"US500":("09:30","16:00"),"GER40":("09:00","17:30")}
if __name__=="__main__":
    for s in ["US100","GER40","US30","US500"]:
        d=load(s); m=d["loc"].dt.strftime("%H:%M")
        o=d[m==SES[s][0]]
        print(s,len(d),d.time.min(),d.time.max(),"dias apertura",len(o),"spread mediano apertura",o.spread.median(),"precio",o.open.median())
