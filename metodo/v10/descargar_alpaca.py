"""v10-bis: volumen con signo de QQQ en 9:30-9:40 ET desde Alpaca (cuenta de papel gratis, SIP histórico).
Uso: python descargar_alpaca.py AÑO  (secretos ALPACA_KEY_ID y ALPACA_SECRET). Salida: datos/qqq_delta_AÑO.csv
Regla del tick: precio > anterior = comprador, < = vendedor, igual = el lado anterior. Sin la subasta de apertura
(condiciones Q/O) ni lotes impares (I)."""
import os, sys, time, json, urllib.request, urllib.parse
import pandas as pd

Y = int(sys.argv[1]); OUT = os.path.join(os.path.dirname(__file__), "datos"); os.makedirs(OUT, exist_ok=True)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET"]}
EXCL = {"Q", "O", "I", "M", "6", "9"}


def get(params):
    url = "https://data.alpaca.markets/v2/stocks/trades?" + urllib.parse.urlencode(params)
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("reintento", k, e); time.sleep(5 * (k + 1))
    raise RuntimeError(url)


filas = []
for d in pd.bdate_range(f"{Y}-01-01", min(pd.Timestamp(f"{Y}-12-31"), pd.Timestamp("2026-11-13"))):
    a = pd.Timestamp(d.year, d.month, d.day, 9, 30, tz="America/New_York").tz_convert("UTC")
    p = dict(symbols="QQQ", start=a.isoformat().replace("+00:00", "Z"),
             end=(a + pd.Timedelta(minutes=10)).isoformat().replace("+00:00", "Z"), limit=10000, feed="sip")
    tr = []
    while True:
        j = get(p); tr += j.get("trades", {}).get("QQQ", []) or []
        if not j.get("next_page_token"):
            break
        p["page_token"] = j["next_page_token"]; time.sleep(0.31)
    time.sleep(0.31)
    if len(tr) < 50:
        continue
    x = pd.DataFrame(tr); x["t"] = pd.to_datetime(x.t)
    x = x[~x.c.apply(lambda c: bool(set(c or []) & EXCL))].sort_values("t")
    dp = x.p.diff(); lado = dp.apply(lambda v: 1 if v > 0 else (-1 if v < 0 else 0)).replace(0, pd.NA).ffill().fillna(0)
    m5 = x.t < a + pd.Timedelta(minutes=5)
    filas.append(dict(fecha=d.date(), o=x.p.iloc[0], c=x.p.iloc[-1], vol=x.s.sum(), delta=(lado * x.s).sum(),
                      vol5=x.s[m5].sum(), delta5=(lado[m5] * x.s[m5]).sum(), n=len(x)))
    if len(filas) % 20 == 0:
        print(d.date(), len(filas), flush=True)
pd.DataFrame(filas).to_csv(f"{OUT}/qqq_delta_{Y}.csv", index=False); print("días", len(filas))
