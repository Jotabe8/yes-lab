"""Momentum intradía en BTC (Shen, Urquhart y Wang, 2022) con las reglas de
informes/btc-intradia-preregistro.md.

Regla principal: el signo del retorno de 00:00 a 00:30 UTC decide la dirección de la última
media hora (23:30 a 24:00). Regla secundaria: el signo de r1 + rN-1 (23:00 a 23:30).

Uso:
    python -m lab.btc_intradia
    python -m lab.btc_intradia --cost 0.10
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict

from lab.intradia import load

CORTE = "2021-01-01"


def daily_returns(bars: list[tuple[str, float, float]]) -> dict[str, dict[str, float]]:
    """Por día UTC: r1 (00:00), rN1 (23:00) y rN (23:30), retornos de vela apertura→cierre en %."""
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for t, o, c in bars:
        hhmm = t[11:16]
        key = {"00:00": "r1", "23:00": "rN1", "23:30": "rN"}.get(hhmm)
        if key and o > 0:
            out[t[:10]][key] = (c / o - 1) * 100
    return {d: v for d, v in out.items() if len(v) == 3}


def trades(days: dict[str, dict[str, float]], regla: str, cost: float) -> list[tuple[str, float]]:
    res = []
    for d in sorted(days):
        v = days[d]
        x = v["r1"] if regla == "principal" else v["r1"] + v["rN1"]
        if x == 0:
            continue
        res.append((d, math.copysign(1, x) * v["rN"] - cost))
    return res


def stats(pnls: list[float]) -> dict[str, float]:
    n = len(pnls)
    m = sum(pnls) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in pnls) / (n - 1))
    return {"n": n, "media": m, "t": m / (sd / math.sqrt(n)), "acierto": sum(x > 0 for x in pnls) / n * 100}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cost", type=float, default=0.05, help="%% por operación completa")
    a = ap.parse_args(argv)
    days = daily_returns(load("BTCUSDT", "30m"))
    print(f"BTCUSDT 30m, {min(days)} a {max(days)}, {len(days)} días completos. % por operación.")
    for regla in ("principal", "secundaria"):
        for cost in (0.0, a.cost, 2 * a.cost):
            tr = trades(days, regla, cost)
            si = stats([p for d, p in tr if d < CORTE])
            so = stats([p for d, p in tr if d >= CORTE])
            ok = so["media"] > 0 and so["t"] > 2 and si["media"] > 0
            print(f"{regla:<10} coste {cost:.2f}  IS n {si['n']} media {si['media']:+.4f} t {si['t']:+.2f}  "
                  f"OOS n {so['n']} media {so['media']:+.4f} t {so['t']:+.2f} acierto {so['acierto']:.0f}%"
                  f"{'  PASA' if ok and cost == a.cost else ''}")
        for year in range(2017, 2027):
            tr = [p for d, p in trades(days, regla, a.cost) if d.startswith(str(year))]
            if len(tr) > 1:
                s = stats(tr)
                print(f"   {year}: n {s['n']} media {s['media']:+.4f} t {s['t']:+.2f}")


if __name__ == "__main__":
    main()
