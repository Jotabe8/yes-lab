import os, json, urllib.request, pandas as pd, yfinance as yf
OUT = "metodo/v4/datos/sub"; os.makedirs(OUT, exist_ok=True)
filas, pag = [], 1
while True:
    u = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
         f"?fields=auction_date,security_type,security_term,reopening,inflation_index_security,floating_rate&page[size]=5000&page[number]={pag}")
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120))
    filas += j["data"]; print(pag, len(j["data"]), flush=True)
    if pag >= j["meta"]["total-pages"]: break
    pag += 1
pd.DataFrame(filas).to_csv(f"{OUT}/subastas.csv", index=False)
for s in "IEF TLT IEI SHY ZN=F ZB=F ZF=F".split():
    d = yf.download(s, start="2000-01-01", auto_adjust=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d.to_csv(f"{OUT}/{s.replace('=','_')}.csv"); print(s, len(d))
