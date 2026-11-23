"""v20: barras de 1 min (SIP, sin ajustar) de un ETF desde Alpaca, sesión 9:30-15:59 NY.
Uso: alpaca_barras.py SIMBOLO salida.npz (secretos ALPACA_KEY_ID y ALPACA_SECRET).
Salida: fechas (str), x (días, 390, 5) = o, h, l, c, volumen."""
import os, sys, time, json, urllib.request, urllib.parse
import numpy as np, pandas as pd
S, sal = sys.argv[1], sys.argv[2]
H = {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET"]}

def get(p):
    url = "https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(p)
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("reintento", k, e); time.sleep(5 * (k + 1))
    raise RuntimeError(url)

filas = []
for ini in pd.date_range("2016-01-01", "2026-11-01", freq="MS"):
    fin = min(ini + pd.offsets.MonthBegin(1), pd.Timestamp("2026-11-14"))
    p = dict(symbols=S, timeframe="1Min", start=ini.strftime("%Y-%m-%dT00:00:00Z"), end=fin.strftime("%Y-%m-%dT00:00:00Z"),
             limit=10000, feed="sip", adjustment="raw")
    while True:
        j = get(p); filas += j.get("bars", {}).get(S, []) or []
        if not j.get("next_page_token"):
            break
        p["page_token"] = j["next_page_token"]; time.sleep(0.31)
    time.sleep(0.31); print(ini.date(), len(filas), flush=True)
df = pd.DataFrame(filas)
df.index = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
t = df.index.hour * 60 + df.index.minute
df = df[(t >= 570) & (t < 960)]
fechas, arr = [], []
for f, g in df.groupby(df.index.date):
    x = np.full((390, 5), np.nan, np.float32)
    k = (g.index.hour * 60 + g.index.minute).values - 570
    x[k] = g[["o", "h", "l", "c", "v"]].values
    fechas.append(str(f)); arr.append(x)
np.savez_compressed(sal, fechas=np.array(fechas), x=np.array(arr))
print(S, len(fechas))
