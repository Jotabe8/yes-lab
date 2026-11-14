import os, pandas as pd, yfinance as yf
OUT = "metodo/v4/datos/bab"; os.makedirs(OUT, exist_ok=True)
S = "XLB XLE XLF XLI XLK XLP XLU XLV XLY SPY ^IRX EWA EWC EWD EWG EWH EWI EWJ EWK EWL EWM EWN EWO EWP EWQ EWS EWU EWW EWY EWT EWZ".split()
for s in S:
    d = yf.download(s, start="1995-01-01", auto_adjust=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d.to_csv(f"{OUT}/bab_{s.replace('^','')}.csv"); print(s, len(d))
