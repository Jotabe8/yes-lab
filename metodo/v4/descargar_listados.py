"""Ronda 5: velas diarias y financiación de los primeros 4 meses de cada perpetuo USDT-M de Binance + BTC completo."""
import io, os, re, zipfile, datetime as dt, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
OUT = "metodo/v4/datos/lis"; os.makedirs(OUT, exist_ok=True)
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
        x = None
        for _ in range(5):
            x = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}&marker={marker}")
            if x: break
            time.sleep(5)
        x = x.decode()
        out += re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:]
        if "<IsTruncated>true</IsTruncated>" not in x: break
        marker = re.findall(r"<NextMarker>([^<]+)</NextMarker>", x)[0]
    return [q.rstrip("/").split("/")[-1] for q in out]
def meses_de(sym):
    x = None
    for _ in range(4):
        x = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/monthly/klines/{sym}/1d/")
        if x: break
        time.sleep(3)
    fs = sorted(re.findall(r"(\d{4}-\d{2})\.zip</Key>", x.decode())) if x else []
    return fs
KC = ["open_time","open","high","low","close","volume","close_time","qv","n","tb","tq","ign"]
def zcsv(b, cols):
    z = zipfile.ZipFile(io.BytesIO(b)); raw = z.read(z.namelist()[0]).decode()
    return pd.read_csv(io.StringIO(raw), header=0 if not raw[:1].isdigit() else None, names=None if not raw[:1].isdigit() else cols)
syms = [s for s in listar("data/futures/um/monthly/klines/") if s.endswith("USDT") and not re.match(r".*_\d+$", s)]
print("símbolos", len(syms), flush=True)
def uno(sym):
    try: return uno_(sym)
    except Exception as e:
        print("fallo", sym, e, flush=True); return sym, None
def uno_(sym):
    fs = meses_de(sym)
    if not fs: return sym, None
    sel = fs if sym == "BTCUSDT" else fs[:4]
    k, f = [], []
    for ym in sel:
        y, m = ym.split("-")
        b = get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1d/{sym}-1d-{ym}.zip")
        if b: k.append(zcsv(b, KC))
        b = get(f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{ym}.zip")
        if b: f.append(zcsv(b, ["calc_time","funding_interval_hours","last_funding_rate"]))
    if k: pd.concat(k).to_csv(f"{OUT}/{sym}_k.csv.gz", index=False)
    if f: pd.concat(f).to_csv(f"{OUT}/{sym}_f.csv.gz", index=False)
    return sym, (fs[0], len(fs))
filas = []
with ThreadPoolExecutor(8) as ex:
    for s, r in ex.map(uno, syms):
        if r: filas.append(dict(sym=s, primer_mes=r[0], meses=r[1]))
pd.DataFrame(filas).to_csv(f"{OUT}/listados.csv", index=False); print("ok", len(filas))
