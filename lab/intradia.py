"""Velas intradía de Binance (sin clave) a datos_intradia/<SYMBOL>_<interval>.csv.gz.

Binance no es accesible desde el entorno de trabajo, así que esta descarga la lanza el workflow
.github/workflows/descargar-intradia.yml, que sube el archivo al repositorio.

Uso:
    python -m lab.intradia BTCUSDT --interval 30m --desde 2017-08-17
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
from pathlib import Path

from lab.fetch import _get_json

DIR = Path(__file__).resolve().parent.parent / "datos_intradia"


def fetch_klines(symbol: str, interval: str, desde: str) -> list[list]:
    start = int(dt.datetime.fromisoformat(desde).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    rows: list[list] = []
    while True:
        url = (
            "https://data-api.binance.vision/api/v3/klines"
            f"?symbol={symbol}&interval={interval}&startTime={start}&limit=1000"
        )
        batch = _get_json(url)
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 1000:
            break
        start = batch[-1][0] + 1
    return rows


def save(symbol: str, interval: str, rows: list[list]) -> Path:
    DIR.mkdir(exist_ok=True)
    path = DIR / f"{symbol}_{interval}.csv.gz"
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "o", "h", "l", "c", "v"])
        for k in rows:
            t = dt.datetime.fromtimestamp(k[0] / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
            w.writerow([t, k[1], k[2], k[3], k[4], k[5]])
    return path


def load(symbol: str, interval: str) -> list[tuple[str, float, float]]:
    """(hora UTC 'AAAA-MM-DD HH:MM', apertura, cierre) por vela."""
    with gzip.open(DIR / f"{symbol}_{interval}.csv.gz", "rt", newline="") as f:
        return [(r["t"], float(r["o"]), float(r["c"])) for r in csv.DictReader(f)]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("symbol")
    ap.add_argument("--interval", default="30m")
    ap.add_argument("--desde", default="2017-08-17")
    a = ap.parse_args(argv)
    rows = fetch_klines(a.symbol, a.interval, a.desde)
    print(f"{len(rows)} velas -> {save(a.symbol, a.interval, rows)}")


if __name__ == "__main__":
    main()
