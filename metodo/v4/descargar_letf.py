import os, pandas as pd, yfinance as yf
OUT = "metodo/v4/datos/letf"; os.makedirs(OUT, exist_ok=True)
for s in "TQQQ SQQQ UPRO SPXU SPXL SPXS UDOW SDOW TNA TZA SOXL SOXS FAS FAZ TECL TECS LABU LABD ERX ERY NUGT DUST YINN YANG QQQ SPY".split():
    d = yf.download(s, start="2010-01-01", auto_adjust=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d.to_csv(f"{OUT}/{s}.csv"); print(s, len(d))
