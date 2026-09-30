"""Descarga cierres diarios de acciones/ETFs, cripto y forex y los guarda como JSON.

Fuentes (ver trading/research/B-datos-y-apis.md):
- Yahoo Finance, endpoint no oficial v8/finance/chart: acciones, índices y forex.
  Solo uso personal; puede devolver 429 o cambiar sin aviso.
- Binance, API pública de datos (data-api.binance.vision): cripto, sin clave.

Salida: docs/data/<id>.json con [{"d": "AAAA-MM-DD", "c": cierre}, ...]
y docs/data/index.json con el catálogo. Los pares forex guardan además apertura,
máximo y mínimo ("o", "h", "l"), que necesita la estrategia NNFX (lab/nnfx.py).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
UA = "Mozilla/5.0 (laboratorio-trading; uso personal)"

# id, nombre visible, mercado, fuente, símbolo en la fuente
INSTRUMENTS = [
    ("spy", "SPY (S&P 500 ETF)", "acciones", "yahoo", "SPY"),
    ("ibex", "IBEX 35", "acciones", "yahoo", "^IBEX"),
    ("san", "Banco Santander", "acciones", "yahoo", "SAN.MC"),
    ("btc", "Bitcoin (BTC/USDT)", "cripto", "binance", "BTCUSDT"),
    ("eth", "Ether (ETH/USDT)", "cripto", "binance", "ETHUSDT"),
    ("eurusd", "EUR/USD", "forex", "yahoo", "EURUSD=X"),
    ("gbpusd", "GBP/USD", "forex", "yahoo", "GBPUSD=X"),
    ("usdjpy", "USD/JPY", "forex", "yahoo", "JPY=X"),
    ("nzdusd", "NZD/USD", "forex", "yahoo", "NZDUSD=X"),
    ("usdchf", "USD/CHF", "forex", "yahoo", "CHF=X"),
    ("euraud", "EUR/AUD", "forex", "yahoo", "EURAUD=X"),
    ("gbpjpy", "GBP/JPY", "forex", "yahoo", "GBPJPY=X"),
]


def _get_json(url: str, retries: int = 3) -> object:
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {last}")


def fetch_yahoo(symbol: str, years: int, ohlc: bool = False) -> list[dict]:
    sym = urllib.request.quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={years}y&interval=1d"
    payload = _get_json(url)
    result = payload["chart"]["result"][0]
    stamps = result.get("timestamp") or []
    quote = result["indicators"]
    closes = (quote.get("adjclose") or [{}])[0].get("adjclose") or quote["quote"][0]["close"]
    q = quote["quote"][0]
    rows = []
    for i, (ts, close) in enumerate(zip(stamps, closes)):
        if close is None:
            continue
        day = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()
        row = {"d": day, "c": round(float(close), 6)}
        if ohlc:
            # sin ajustar: en forex no hay dividendos, así que casa con el cierre
            o, h, l = q["open"][i], q["high"][i], q["low"][i]
            if None in (o, h, l):
                continue
            row.update(o=round(float(o), 6), h=round(float(max(h, o, close)), 6), l=round(float(min(l, o, close)), 6))
        rows.append(row)
    return dedupe(rows)


def fetch_binance(symbol: str, years: int) -> list[dict]:
    start = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=365 * years)).timestamp() * 1000)
    rows: list[dict] = []
    while True:
        url = (
            "https://data-api.binance.vision/api/v3/klines"
            f"?symbol={symbol}&interval=1d&startTime={start}&limit=1000"
        )
        batch = _get_json(url)
        if not batch:
            break
        for k in batch:
            day = dt.datetime.fromtimestamp(k[0] / 1000, dt.timezone.utc).date().isoformat()
            rows.append({"d": day, "c": float(k[4])})
        if len(batch) < 1000:
            break
        start = batch[-1][0] + 1
    return dedupe(rows)


def dedupe(rows: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for r in rows:
        seen[r["d"]] = r
    return [seen[d] for d in sorted(seen)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--only", nargs="*", help="ids a descargar (por defecto todos)")
    args = ap.parse_args(argv)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index, failures = [], []
    for ident, name, market, source, symbol in INSTRUMENTS:
        if args.only and ident not in args.only:
            continue
        try:
            rows = (fetch_yahoo(symbol, args.years, ohlc=market == "forex") if source == "yahoo"
                    else fetch_binance(symbol, args.years))
            if len(rows) < 30:
                raise RuntimeError(f"solo {len(rows)} filas")
        except Exception as exc:  # un instrumento caído no debe tumbar el resto
            failures.append(f"{ident}: {exc}")
            print(f"ERROR {ident}: {exc}", file=sys.stderr)
            continue
        (DATA_DIR / f"{ident}.json").write_text(json.dumps(rows, separators=(",", ":")))
        index.append({"id": ident, "name": name, "market": market, "source": source,
                      "symbol": symbol, "first": rows[0]["d"], "last": rows[-1]["d"], "n": len(rows)})
        print(f"OK {ident}: {len(rows)} filas, {rows[0]['d']} a {rows[-1]['d']}")

    if index:
        old = {}
        idx_path = DATA_DIR / "index.json"
        if idx_path.exists():
            old = {i["id"]: i for i in json.loads(idx_path.read_text()).get("series", [])}
        old.update({i["id"]: i for i in index})
        meta = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "series": [old[k] for k in sorted(old)]}
        idx_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False))

    return 1 if failures and not index else 0


if __name__ == "__main__":
    sys.exit(main())
