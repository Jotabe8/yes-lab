# Barras de 30 min (hora servidor NY+7) con spread medio, desde M1
import pandas as pd, sys, os
D="../../data"
FILES={"US500":"USA500IDXUSD_M1_DUKA.csv","US30":"USA30IDXUSD_M1_DUKA.csv","US2000":"USSC2000IDXUSD_M1_DUKA.csv",
 "UK100":"GBRIDXGBP_M1_DUKA.csv","FRA40":"FRAIDXEUR_M1_DUKA.csv","EU50":"EUSIDXEUR_M1_DUKA.csv","JP225":"JPNIDXJPY_M1_DUKA.csv",
 "USOIL":"USOIL_M1_FTMO.csv","GER40":"DEUIDXEUR_M1_DUKA.csv"}
for k in sys.argv[1:]:
    m=pd.read_csv(f"{D}/{FILES[k]}",parse_dates=["time"],index_col="time")
    if k=="USOIL": m.to_pickle(f"USOIL_M1.pkl")
    b=m.resample("30min").agg({"open":"first","high":"max","low":"min","close":"last","spread":"mean"}).dropna()
    b.to_pickle(f"b30_{k}.pkl"); print(k,len(b),b.index.min(),b.index.max(),b.spread.median(),b.close.median(),flush=True)
