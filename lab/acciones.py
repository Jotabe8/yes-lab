"""Descarga velas diarias OHLCV de acciones de EE. UU. desde Yahoo para el estudio del gap de resultados.

Yahoo no es accesible desde el entorno de trabajo de Claude: esto corre en GitHub
(workflow descargar-acciones.yml) y guarda datos_acciones/<TICKER>.csv.

Los precios OHLC de Yahoo vienen ajustados por splits pero no por dividendos, que es lo que
hace falta para medir gaps de apertura.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

from lab.fetch import _get_json

OUT_DIR = Path(__file__).resolve().parent.parent / "datos_acciones"

# Acciones de EE. UU. que FTMO ofrece como CFD (lista a confirmar en el terminal de Jorge).
FTMO = ["AAPL", "AMZN", "BABA", "BAC", "GOOG", "META", "MSFT", "NFLX", "NVDA", "PFE",
        "T", "TSLA", "V", "WMT", "ZM", "BA", "KO", "DIS", "INTC", "AMD", "NKE", "JPM", "PYPL"]
# Resto de grandes compañías, solo para tener potencia estadística al medir el efecto.
AMPLIO = ["ABBV", "ABT", "ACN", "ADBE", "AVGO", "C", "CAT", "CMCSA", "COST", "CRM", "CSCO",
          "CVX", "GE", "GS", "HD", "IBM", "JNJ", "LLY", "LOW", "MA", "MCD", "MDT", "MMM", "MO",
          "MRK", "MS", "ORCL", "PEP", "PG", "QCOM", "SBUX", "TGT", "TMO", "TXN", "UNH", "UNP",
          "UPS", "USB", "VZ", "WFC", "XOM", "GILD", "AMGN", "BMY", "HON", "LMT", "F", "GM"]
REFERENCIA = ["QQQ", "SPY"]


def fetch(symbol: str, desde: dt.date) -> list[list]:
    p1 = int(dt.datetime.combine(desde, dt.time(), dt.timezone.utc).timestamp())
    p2 = int(dt.datetime.now(dt.timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={p1}&period2={p2}&interval=1d")
    result = _get_json(url)["chart"]["result"][0]
    q = result["indicators"]["quote"][0]
    rows = []
    for i, ts in enumerate(result.get("timestamp") or []):
        o, h, l, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
        if None in (o, h, l, c, v) or o <= 0:
            continue
        day = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()
        rows.append([day, round(o, 4), round(h, 4), round(l, 4), round(c, 4), int(v)])
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde", default="2005-01-01")
    args = ap.parse_args(argv)
    desde = dt.date.fromisoformat(args.desde)
    OUT_DIR.mkdir(exist_ok=True)
    fallos = 0
    for sym in FTMO + AMPLIO + REFERENCIA:
        try:
            rows = fetch(sym, desde)
        except Exception as exc:  # un ticker caído no debe tumbar el resto
            print(f"ERROR {sym}: {exc}", file=sys.stderr)
            fallos += 1
            continue
        with open(OUT_DIR / f"{sym}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["d", "o", "h", "l", "c", "v"])
            w.writerows(rows)
        print(f"OK {sym}: {len(rows)} filas, {rows[0][0]} a {rows[-1][0]}")
    return 1 if fallos > 10 else 0


if __name__ == "__main__":
    sys.exit(main())
