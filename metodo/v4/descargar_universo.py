"""Universo nuevo de perpetuos Binance (ronda 4). Paralelo con hilos."""
import io, os, re, zipfile, datetime as dt, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
OUT = "metodo/v4/datos/uni"; os.makedirs(OUT, exist_ok=True)
VISTOS = {"BTC","ETH","BNB","SOL","XRP","ADA","DOGE","LTC","LINK","DOT","AVAX","TRX","BCH","ETC","XLM","ATOM","EOS","FIL","UNI","NEAR"}
ESTABLES = {"USDC","BUSD","TUSD","USDP","DAI","FDUSD","USDE"}
def get(url):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
        except Exception: pass
        time.sleep(1 + k)
def listar(prefix):
    out, marker = [], ""
    while True:
        x = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}&marker={marker}").decode()
        p = re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:]
        out += p
        if "<IsTruncated>true</IsTruncated>" not in x: break
        marker = re.findall(r"<NextMarker>([^<]+)</NextMarker>", x)[0]
    return [q.rstrip("/").split("/")[-1] for q in out]
syms = [s for s in listar("data/futures/um/monthly/klines/") if s.endswith("USDT") and not re.match(r".*_\d+$", s)]
base = {s: s[:-4] for s in syms}
syms = [s for s in syms if base[s] not in VISTOS and base[s] not in ESTABLES and not base[s].startswith("1000")]
print("candidatos", len(syms))
hoy = dt.date.today(); meses = [(y, m) for y in range(2019, hoy.year + 1) for m in range(1, 13) if dt.date(y, m, 1) < hoy.replace(day=1)]
KC = ["open_time","open","high","low","close","volume","close_time","qv","n","tb","tq","ign"]
def zcsv(b, cols):
    raw = zipfile.ZipFile(io.BytesIO(b)); raw = raw.read(raw.namelist()[0]).decode()
    return pd.read_csv(io.StringIO(raw), header=0 if not raw[:1].isdigit() else None, names=None if not raw[:1].isdigit() else cols)
def uno(sym):
    b0 = get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1d/{sym}-1d-2022-12.zip")
    if b0 is None: return sym, 0
    res = {}
    for nom, url, cols in (("perp1d", "futures/um/monthly/klines/{s}/1d/{s}-1d-{y}-{m:02d}.zip", KC),
                           ("spot1d", "spot/monthly/klines/{s}/1d/{s}-1d-{y}-{m:02d}.zip", KC),
                           ("funding", "futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{y}-{m:02d}.zip", ["calc_time","funding_interval_hours","last_funding_rate"])):
        l = []
        for y, m in meses:
            b = get("https://data.binance.vision/data/" + url.format(s=sym, y=y, m=m))
            if b: l.append(zcsv(b, cols))
        if l: pd.concat(l).to_csv(f"{OUT}/{sym[:-4]}_{nom}.csv.gz", index=False); res[nom] = len(l)
    return sym, res
with ThreadPoolExecutor(16) as ex:
    for s, r in ex.map(uno, syms): print(s, r, flush=True)
