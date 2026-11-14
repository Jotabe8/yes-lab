"""Descarga de datos para la búsqueda v4 (primas de riesgo). Se ejecuta en GitHub Actions
(el contenedor no tiene red). Salida en metodo/v4/datos/.
- CBOE: índices VIX, VIX9D, VIX3M, VIX6M (diarios) y liquidaciones diarias de cada vencimiento del futuro VX.
- Yahoo: SVXY, VXX, VIXY, SPY (diarios, ajustados).
- Binance data vision: tasas de financiación de perpetuos USDT-M y velas diarias spot y perpetuo.
"""
import io, os, sys, zipfile, datetime as dt, time
import urllib.request
import pandas as pd

OUT = "metodo/v4/datos"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}

def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    return None

def cboe():
    for ix in ("VIX", "VIX9D", "VIX3M", "VIX6M"):
        b = get(f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{ix}_History.csv")
        print(ix, None if b is None else len(b))
        if b: open(f"{OUT}/{ix}_History.csv", "wb").write(b)
    # futuros VX: vencimiento = miércoles 30 días antes del 3er viernes del mes siguiente
    filas = []
    for y in range(2013, 2028):
        for mth in range(1, 13):
            ny, nm = (y, mth + 1) if mth < 12 else (y + 1, 1)
            d1 = dt.date(ny, nm, 1)
            fri3 = d1 + dt.timedelta(days=(4 - d1.weekday()) % 7 + 14)
            exp = fri3 - dt.timedelta(days=30)
            if exp > dt.date(2027, 6, 30): continue
            got = None
            for off in (0, -1, 1, -2):
                e = exp + dt.timedelta(days=off)
                b = get(f"https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{e:%Y-%m-%d}.csv")
                if b:
                    got = (e, b); break
            if got is None:
                print("VX sin datos", exp); continue
            df = pd.read_csv(io.BytesIO(got[1]))
            df["expiry"] = got[0]
            filas.append(df)
    vx = pd.concat(filas)
    vx.to_csv(f"{OUT}/VX_futuros.csv.gz", index=False)
    print("VX filas", len(vx), vx.expiry.nunique())

def yahoo():
    import yfinance as yf
    for s in ("SVXY", "VXX", "VIXY", "SPY", "^VIX", "SVIX", "UVXY"):
        try:
            d = yf.download(s, start="2009-01-01", auto_adjust=False, progress=False)
            if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
            d.to_csv(f"{OUT}/yahoo_{s.replace('^','')}.csv"); print(s, len(d))
        except Exception as e:
            print("yahoo falla", s, e)

SYMS = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LTC", "LINK", "DOT", "AVAX", "TRX", "BCH", "ETC", "XLM", "ATOM", "EOS", "FIL", "UNI", "NEAR"]

def zipcsv(b, cols=None):
    z = zipfile.ZipFile(io.BytesIO(b)); n = z.namelist()[0]
    raw = z.read(n).decode()
    has_header = not raw[:1].isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if has_header else None, names=None if has_header else cols)

KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qv", "n", "tb", "tq", "ign"]

def binance():
    base = "https://data.binance.vision/data"
    hoy = dt.date.today()
    meses = [(y, m) for y in range(2019, hoy.year + 1) for m in range(1, 13) if dt.date(y, m, 1) < hoy.replace(day=1)]
    for s in SYMS:
        sym = s + "USDT"
        fr, ks, kp = [], [], []
        for y, m in meses:
            b = get(f"{base}/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02d}.zip")
            if b: fr.append(zipcsv(b, ["calc_time", "funding_interval_hours", "last_funding_rate"]))
            b = get(f"{base}/spot/monthly/klines/{sym}/1d/{sym}-1d-{y}-{m:02d}.zip")
            if b: ks.append(zipcsv(b, KCOLS))
            b = get(f"{base}/futures/um/monthly/klines/{sym}/1d/{sym}-1d-{y}-{m:02d}.zip")
            if b: kp.append(zipcsv(b, KCOLS))
        for nom, l in (("funding", fr), ("spot1d", ks), ("perp1d", kp)):
            if l: pd.concat(l).to_csv(f"{OUT}/bn_{s}_{nom}.csv.gz", index=False)
        print(s, len(fr), len(ks), len(kp)); sys.stdout.flush()

if __name__ == "__main__":
    que = sys.argv[1]
    {"cboe": cboe, "yahoo": yahoo, "binance": binance}[que]()
