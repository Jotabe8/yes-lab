"""Segunda ronda de ideas, con las reglas de informes/ronda2-preregistro.md.

A. Rebalanceo de coberturas a fin de mes en forex (Melvin y Prins, 2015), D1 de Dukascopy.
B. Prima nocturna de US500 y US100: largo de 16:00 a 09:30 de Nueva York, lunes a jueves.
C. Oro largo en la sesión asiática: de 17:00 de Nueva York a 08:00 de Londres, lunes a jueves.

Las velas M1 están en hora del servidor (Nueva York + 7 h todo el año, comprobado con la
volatilidad del minuto de apertura y cierre de contado del US500 en enero y julio). Los datos
son del PC de Jorge y no se suben al repositorio.

Uso:
    python -m lab.ronda2 a
    python -m lab.ronda2 b --m1 ruta/USA500IDXUSD_M1_DUKA.csv
    python -m lab.ronda2 c --m1 ruta/XAUUSD_M1_DUKA.csv
"""

from __future__ import annotations

import argparse
import csv
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from lab.pares import DATOS, load as load_d1

CORTE = "2020-01-01"
NY, LDN = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
SERVER_OFFSET = timedelta(hours=7)  # hora del servidor = hora de Nueva York + 7 h

FIN_DE_MES = [  # par, índice extranjero, signo de la operación si EE. UU. ha ido mejor
    ("EURUSD", "EUSIDXEUR", 1),
    ("GBPUSD", "GBRIDXGBP", 1),
    ("AUDUSD", "AUSIDXAUD", 1),
    ("USDJPY", "JPNIDXJPY", -1),
]


def stats(pnls: list[float]) -> dict[str, float]:
    n = len(pnls)
    if n < 2:
        return {"n": n, "media": sum(pnls) / n if n else 0.0, "t": 0.0, "acierto": 0.0}
    m = sum(pnls) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in pnls) / (n - 1))
    return {"n": n, "media": m, "t": m / (sd / math.sqrt(n)) if sd else 0.0,
            "acierto": sum(x > 0 for x in pnls) / n * 100}


def report(title: str, trades: list[tuple[str, float]], costs: tuple[float, ...], cost_fn) -> None:
    print(title)
    for k in costs:
        pn = [(d, p - cost_fn(d, k)) for d, p in trades]
        si = stats([p for d, p in pn if d < CORTE])
        so = stats([p for d, p in pn if d >= CORTE])
        ok = si["n"] > 1 and si["media"] > 0 and so["media"] > 0 and so["t"] > 2
        print(f"  costes x{k:g}: IS n {si['n']} media {si['media']:+.4f} % t {si['t']:+.2f} | "
              f"OOS n {so['n']} media {so['media']:+.4f} % t {so['t']:+.2f} acierto {so['acierto']:.0f}%"
              f"{'  PASA' if ok and k == 1 else ''}")


# --- A. Fin de mes en forex -------------------------------------------------------------

def last_close_before(series: dict[str, tuple[float, float]], dates: list[str], d: str) -> float | None:
    """Último cierre del índice en una fecha <= d (dates ordenadas)."""
    lo, hi = 0, len(dates)
    while lo < hi:
        mid = (lo + hi) // 2
        if dates[mid] <= d:
            lo = mid + 1
        else:
            hi = mid
    return series[dates[lo - 1]][1] if lo else None


def month_end_trades(pair: str, foreign: str, sign: int, datos: Path = DATOS) -> list[tuple[str, float, int]]:
    """(fecha de entrada, retorno bruto en %, noches) por mes."""
    fx = load_d1(pair, datos)
    us, fo = load_d1("USA500IDXUSD", datos), load_d1(foreign, datos)
    us_d, fo_d = sorted(us), sorted(fo)
    days = sorted(fx)
    months: dict[str, list[str]] = {}
    for d in days:
        months.setdefault(d[:7], []).append(d)
    keys = sorted(months)
    out = []
    for prev, cur in zip(keys, keys[1:-1]):  # el último mes puede estar incompleto
        s = months[cur]
        if len(s) < 5:
            continue
        signal, entry, exit_ = s[-3], s[-2], s[-1]
        base = months[prev][-1]
        vals = [last_close_before(us, us_d, signal), last_close_before(us, us_d, base),
                last_close_before(fo, fo_d, signal), last_close_before(fo, fo_d, base)]
        if None in vals:
            continue
        us_ret = vals[0] / vals[1] - 1
        fo_ret = vals[2] / vals[3] - 1
        if us_ret == fo_ret:
            continue
        side = sign if us_ret > fo_ret else -sign
        ret = side * (fx[exit_][1] / fx[entry][0] - 1) * 100
        nights = (date.fromisoformat(exit_) - date.fromisoformat(entry)).days
        out.append((entry, ret, nights))
    return out


def run_a(datos: Path) -> None:
    allt: list[tuple[str, float]] = []
    nights: dict[str, int] = {}
    for pair, foreign, sign in FIN_DE_MES:
        tr = month_end_trades(pair, foreign, sign, datos)
        report(f"A · {pair} frente a {foreign}", [(d, r) for d, r, _ in tr], (0, 1, 2),
               lambda d, k, n={f"{pair}{d}": x for d, _, x in tr}, p=pair: k * (0.02 + 0.01 * n[f"{p}{d}"]))
        for d, r, x in tr:
            allt.append((f"{d}|{pair}", r))
            nights[f"{d}|{pair}"] = x
    report("A · los 4 pares juntos", allt, (0, 1, 2), lambda d, k: k * (0.02 + 0.01 * nights[d]))


# --- B y C. Velas M1 ----------------------------------------------------------------------

def read_m1(path: Path) -> dict[str, tuple[float, float, float]]:
    """{'AAAA-MM-DD HH:MM' hora servidor: (open, close, spread)}. Ignora las filas diarias."""
    out = {}
    with open(path, newline="") as f:
        r = csv.reader(f)
        head = next(r)
        sp = head.index("spread") if "spread" in head else None
        for row in r:
            t = row[0][:16]
            out[t] = (float(row[1]), float(row[4]), float(row[sp]) if sp is not None else 0.0)
    return out


def server(ny_dt: datetime) -> str:
    return (ny_dt.replace(tzinfo=None) + SERVER_OFFSET).strftime("%Y-%m-%d %H:%M")


def nearest(bars: dict, key: str, back: int = 5, forward: int = 0) -> tuple[str, tuple] | None:
    """La vela en `key` o, si falta, la más cercana hacia atrás (o hacia delante)."""
    t = datetime.strptime(key, "%Y-%m-%d %H:%M")
    for i in range(0, back + 1):
        k = (t - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M")
        if k in bars:
            return k, bars[k]
    for i in range(1, forward + 1):
        k = (t + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M")
        if k in bars:
            return k, bars[k]
    return None


def session_days(bars: dict) -> list[date]:
    return sorted({date.fromisoformat(k[:10]) for k in bars})


def overnight_trades(bars: dict) -> list[tuple[str, float]]:
    """Largo del cierre de contado (vela 15:59 NY) a la apertura siguiente (vela 09:30 NY)."""
    out = []
    days = set(session_days(bars))
    for d in sorted(days):
        if d.weekday() > 3:
            continue
        nxt = d + timedelta(days=1)
        if nxt not in days:
            continue
        e = nearest(bars, server(datetime(d.year, d.month, d.day, 15, 59)), back=3)
        x = nearest(bars, server(datetime(nxt.year, nxt.month, nxt.day, 9, 30)), back=0, forward=2)
        # sesión de contado de verdad: debe haber velas a las 09:30 NY de ambos días
        if not e or not x or not nearest(bars, server(datetime(d.year, d.month, d.day, 9, 30)), back=0, forward=2):
            continue
        out.append((d.isoformat(), (x[1][0] / e[1][1] - 1) * 100))
    return out


def asia_gold_trades(bars: dict) -> list[tuple[str, float, float]]:
    """Largo desde la última vela antes de las 17:00 NY hasta la apertura de las 08:00 de Londres."""
    out = []
    days = set(session_days(bars))
    for d in sorted(days):
        if d.weekday() > 3:
            continue
        nxt = d + timedelta(days=1)
        e = nearest(bars, server(datetime(d.year, d.month, d.day, 16, 59)), back=10)
        ldn = datetime(nxt.year, nxt.month, nxt.day, 8, 0, tzinfo=LDN).astimezone(NY)
        x = nearest(bars, server(ldn), back=0, forward=5)
        if not e or not x:
            continue
        o_exit = x[1][0]
        c_entry, spread_entry = e[1][1], e[1][2]
        gross = (o_exit / c_entry - 1) * 100
        # Los precios son bid: se compra al ask de entrada (bid + spread) y se vende al bid de salida.
        cost = spread_entry / c_entry * 100
        out.append((d.isoformat(), gross, cost))
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("idea", choices=["a", "b", "c"])
    ap.add_argument("--datos", type=Path, default=DATOS)
    ap.add_argument("--m1", type=Path, action="append", default=[])
    a = ap.parse_args(argv)
    if a.idea == "a":
        run_a(a.datos)
    elif a.idea == "b":
        for path in a.m1:
            tr = overnight_trades(read_m1(path))
            report(f"B · prima nocturna {path.name}, {tr[0][0]} a {tr[-1][0]}", tr, (0, 1, 2),
                   lambda d, k: k * (0.02 + 0.015))
            for year in sorted({d[:4] for d, _ in tr}):
                s = stats([p - 0.035 for d, p in tr if d.startswith(year)])
                print(f"     {year}: n {s['n']} media neta {s['media']:+.4f} % t {s['t']:+.2f}")
    else:
        for path in a.m1:
            tr = asia_gold_trades(read_m1(path))
            costs = {d: c for d, _, c in tr}
            report(f"C · oro en Asia {path.name}, {tr[0][0]} a {tr[-1][0]}", [(d, g) for d, g, _ in tr], (0, 1, 2),
                   lambda d, k: k * (costs[d] + 0.01))
            for year in sorted({d[:4] for d, _, _ in tr}):
                s = stats([g - c - 0.01 for d, g, c in tr if d.startswith(year)])
                print(f"     {year}: n {s['n']} media neta {s['media']:+.4f} % t {s['t']:+.2f}")


if __name__ == "__main__":
    main()
