import os, pandas as pd, yfinance as yf
OUT = "metodo/v4/datos/ene"; os.makedirs(OUT, exist_ok=True)
for s in "IWM SPY ^RUT ^GSPC IJR".split():
    d = yf.download(s, start="1985-01-01", auto_adjust=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d.to_csv(f"{OUT}/ene_{s.replace('^','')}.csv"); print(s, len(d))
