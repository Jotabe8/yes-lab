"""El ORB de US100 en otros índices y con más historia, sin reajustar nada.

Misma regla que `lab.us100` (ORB_US100 v0.16 por defecto: rango de 10 minutos desde la apertura
cash, dirección de la vela, stop al 15% del ATR(14) diario, sin objetivo, riesgo 0.5%). Lo único
que se traduce a cada mercado es el reloj:

- US100, US500 y US30: apertura 16:30 del servidor y cierre a las 22:30, como el EA.
- GER40: apertura de Xetra (09:00 de Fráncfort, 10:00 del servidor) y cierre 30 minutos antes
  del cierre de Xetra (18:00 del servidor), igual que el EA sale 30 minutos antes del cierre de
  Nueva York. El servidor sigue el horario de verano de EE. UU.; las semanas en que Europa aún no
  ha cambiado de hora (marzo) o ya lo ha hecho (finales de octubre), la sesión cae una hora más
  tarde y se desplaza con `Day.shift`.

Festivos: calendario de la NYSE (con los cierres anticipados que salta el EA) para los índices
de EE. UU. y de Xetra para el GER40, calculados para cualquier año.

Datos (hora del servidor de FTMO, NY+7): velas M1 de FTMO exportadas con `python -m lab.us100
--export --symbol ...` y, para la historia anterior, velas M1 de Dukascopy con el spread real
por minuto. Cada mercado puede juntar varios ficheros con una fecha de corte. El manifiesto por
defecto está en `MANIFEST`; `--manifest fichero.json` lo sustituye.

Costes: spread de la vela de entrada más un deslizamiento fijo por operación proporcional al de
US100 (0.2 puntos a unos 20.000 puntos), "costes al doble" duplica los dos.

Uso:
    python -m lab.orb_indices --data-dir "RUTA/data" > orb_indices.txt
    python -m lab.orb_indices --data-dir "RUTA/data" --only GER40 --monte-carlo 2000
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from dataclasses import replace
from pathlib import Path

from lab.nnfx import metrics, monte_carlo
from lab.us100 import (Bar, Day, OrbConfig, Result, backtest_orb, chain, daily_returns,
                       orb_grid, trade_stats, walk_forward)

# ── Calendarios ──────────────────────────────────────────────────────────────


def easter(y: int) -> dt.date:
    """Domingo de Pascua (algoritmo anónimo gregoriano)."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    return dt.date(y, month, (h + l_ - 7 * m + 114) % 31 + 1)


def _nth_weekday(y: int, month: int, weekday: int, n: int) -> dt.date:
    """n-ésimo `weekday` (0 = lunes) del mes; n = -1 es el último."""
    if n > 0:
        first = dt.date(y, month, 1)
        return first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))
    last = dt.date(y + month // 12, month % 12 + 1, 1) - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def _observed(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=1) if d.weekday() == 5 else d + dt.timedelta(days=1) if d.weekday() == 6 else d


# Cierres extraordinarios de la NYSE (huracán Sandy, funerales de Bush y Carter).
NYSE_SPECIAL = {"2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"}


def nyse_holidays(y: int) -> set[str]:
    """Festivos de la NYSE más los cierres anticipados que el EA trata como festivos.

    Cierres anticipados: el 3 de julio (si es laborable y el 4 no cae en lunes ni es fin de semana
    observado), el viernes después de Acción de Gracias y el 24 de diciembre laborable.
    """
    days = {_observed(dt.date(y, 7, 4)), _observed(dt.date(y, 12, 25)),
            _nth_weekday(y, 1, 0, 3), _nth_weekday(y, 2, 0, 3), easter(y) - dt.timedelta(days=2),
            _nth_weekday(y, 5, 0, -1), _nth_weekday(y, 9, 0, 1)}
    ny = dt.date(y, 1, 1)
    if ny.weekday() != 5:                       # Año Nuevo en sábado no se recupera el viernes
        days.add(_observed(ny))
    if y >= 2022:
        days.add(_observed(dt.date(y, 6, 19)))
    thanks = _nth_weekday(y, 11, 3, 4)
    days |= {thanks, thanks + dt.timedelta(days=1)}
    j3 = dt.date(y, 7, 3)
    if j3.weekday() < 5 and j3 not in days and dt.date(y, 7, 4).weekday() < 5:
        days.add(j3)
    x24 = dt.date(y, 12, 24)
    if x24.weekday() < 5:
        days.add(x24)
    out = {d.isoformat() for d in days}
    return out | {d for d in NYSE_SPECIAL if d.startswith(str(y))}


def xetra_holidays(y: int) -> set[str]:
    e = easter(y)
    days = {dt.date(y, 1, 1), e - dt.timedelta(days=2), e + dt.timedelta(days=1), dt.date(y, 5, 1),
            dt.date(y, 12, 24), dt.date(y, 12, 25), dt.date(y, 12, 26), dt.date(y, 12, 31)}
    return {d.isoformat() for d in days}


def us_dst(d: dt.date) -> bool:
    """Horario de verano de EE. UU.: del 2.º domingo de marzo al 1.er domingo de noviembre."""
    return _nth_weekday(d.year, 3, 6, 2) <= d < _nth_weekday(d.year, 11, 6, 1)


def eu_dst(d: dt.date) -> bool:
    """Horario de verano europeo: del último domingo de marzo al último domingo de octubre."""
    return _nth_weekday(d.year, 3, 6, -1) <= d < _nth_weekday(d.year, 10, 6, -1)


def eu_shift(d: str) -> int:
    """Minutos que la apertura europea se retrasa en hora del servidor (NY+7) ese día."""
    x = dt.date.fromisoformat(d)
    return 60 * (us_dst(x) - eu_dst(x))


YEARS = range(2005, 2031)
US_CAL = frozenset(h for y in YEARS for h in nyse_holidays(y))
DE_CAL = frozenset(h for y in YEARS for h in xetra_holidays(y))

# ── Mercados ─────────────────────────────────────────────────────────────────

US_TIMES = {"session_start": 16 * 60 + 30, "trade_end": 22 * 60, "flat_time": 22 * 60 + 30}
DE_TIMES = {"session_start": 10 * 60, "trade_end": 17 * 60, "flat_time": 18 * 60}

# files: [fichero, factor que pasa la columna spread a precio, desde, hasta]. Gana el primero
# que cubre cada día; los cortes evitan mezclar fuentes el mismo día.
MARKETS = {
    "US100": {"times": US_TIMES, "cal": "us", "slippage": 0.2},
    "US500": {"times": US_TIMES, "cal": "us", "slippage": 0.06},
    "US30": {"times": US_TIMES, "cal": "us", "slippage": 0.45},
    "GER40": {"times": DE_TIMES, "cal": "de", "slippage": 0.25},
}

MANIFEST = {
    "US100": [["US100_M1_DUKA.csv", 1.0, None, "2021-09-14"], ["US100_cash_M1_FTMO.csv", 0.01, "2021-09-14", None]],
    "US500": [["USA500IDXUSD_M1_DUKA.csv", 1.0, None, "2021-09-14"], ["US500_cash_M1_FTMO.csv", 0.01, "2021-09-14", None]],
    "US30": [["USA30IDXUSD_M1_DUKA.csv", 1.0, None, "2021-09-14"], ["US30_cash_M1_FTMO.csv", 0.01, "2021-09-14", None]],
    "GER40": [["DEUIDXEUR_M1_DUKA.csv", 1.0, None, "2022-01-01"], ["GER40_M1_FTMO.csv", 1.0, "2022-01-01", None]],
}

# Corte entre lo que ya se vio al elegir la configuración en US100 y la historia nueva.
SEEN_FROM = "2021-09-14"


def config_for(name: str, risk: float = 0.5) -> OrbConfig:
    m = MARKETS[name]
    return OrbConfig(**m["times"], risk_pct=risk, point=1.0, lot_value=1.0, slippage_pts=m["slippage"],
                     holidays=US_CAL if m["cal"] == "us" else DE_CAL)


def read_m1(path: str | Path, spread_factor: float, since: str | None, until: str | None,
            window: tuple[int, int]) -> dict[str, dict]:
    """CSV M1 (time,open,high,low,close[,tick_volume],spread) → por día, el máximo, mínimo y cierre
    del día entero y solo las velas de `window` (minutos del servidor), con el spread en precio.

    Guardar solo la sesión deja la memoria en una cuarta parte con 15 años de M1.
    """
    days: dict[str, dict] = {}
    lo, hi = window
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            d, t = r["time"][:10], r["time"][11:16]
            if (since and d < since) or (until and d >= until):
                continue
            m = int(t[:2]) * 60 + int(t[3:5])
            h, l_, c = float(r["high"]), float(r["low"]), float(r["close"])
            x = days.get(d)
            if x is None:
                x = days[d] = {"n": 0, "h": h, "l": l_, "c": c, "last": -1, "bars": []}
            x["n"] += 1
            x["h"], x["l"] = max(x["h"], h), min(x["l"], l_)
            if m > x["last"]:
                x["last"], x["c"] = m, c
            if lo <= m <= hi:
                v = int(float(r.get("tick_volume") or r.get("volume") or 0))
                x["bars"].append(Bar(m, float(r["open"]), h, l_, c, v, float(r["spread"]) * spread_factor))
    return days


def build_days(name: str, raw: dict[str, dict], n: int = 14) -> list[Day]:
    """Días con su ATR(n) diario del día anterior (media simple del rango verdadero, como iATR)."""
    out, trs, prev_c = [], [], None
    for d in sorted(raw):
        x = raw[d]
        if x["n"] < 60:
            continue
        trs.append(x["h"] - x["l"] if prev_c is None else max(x["h"], prev_c) - min(x["l"], prev_c))
        prev_c = x["c"]
        if len(trs) - 1 >= n and x["bars"]:
            day = Day(d, sorted(x["bars"], key=lambda b: b.m), sum(trs[-1 - n:-1]) / n)
            if MARKETS[name]["times"] is DE_TIMES:
                day.shift = eu_shift(d)
            out.append(day)
    return out


def _window(name: str) -> tuple[int, int]:
    t = MARKETS[name]["times"]
    return t["session_start"], t["flat_time"] + 60     # +60: desfase de horario europeo


def load_market(name: str, data_dir: Path, manifest: dict) -> tuple[list[Day], list[dict]]:
    merged: dict[str, dict] = {}
    sources = []
    for fname, factor, since, until in manifest[name]:
        p = data_dir / fname
        if not p.exists():
            sources.append({"file": fname, "missing": True})
            continue
        part = read_m1(p, factor, since, until, _window(name))
        new = {d: b for d, b in part.items() if d not in merged}
        merged.update(new)
        if new:
            sources.append({"file": fname, "from": min(new), "to": max(new), "days": len(new)})
    return build_days(name, merged), sources


# ── Informe ──────────────────────────────────────────────────────────────────

def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%"


def summary(res: Result) -> str:
    m, s = metrics(res.equity), trade_stats(res.trades)
    return (f"{res.dates[0]}..{res.dates[-1]} | total {_pct(m['total'])} | CAGR {_pct(m['cagr'])} | caída "
            f"{_pct(m['max_drawdown'])} | Sharpe {m['sharpe']:.2f} | PF {s['pf']:.2f} | {s['trades']} ops | "
            f"R medio {s['mean_r']:+.3f} (t {s['t']:.1f})")


def by_year(r1: Result, r2: Result) -> list[str]:
    rows = []
    for y in sorted({t.d[:4] for t in r1.trades}):
        a = trade_stats([t for t in r1.trades if t.d[:4] == y])
        b = trade_stats([t for t in r2.trades if t.d[:4] == y])
        rows.append(f"    {y}: {a['trades']:3d} ops | PF {a['pf']:.2f} | R medio {a['mean_r']:+.3f} | "
                    f"x2 {b['mean_r']:+.3f}")
    return rows


def entry_spread_median(days: list[Day], cfg: OrbConfig, since: str | None = None, until: str | None = None) -> float:
    from lab.us100 import orb_signal
    sp = sorted(d.bars[s["k"]].sp for d in days if (not since or d.d >= since) and (not until or d.d < until)
                and (s := orb_signal(d, cfg)))
    return sp[len(sp) // 2] if sp else float("nan")


def overlap_check(name: str, data_dir: Path, manifest: dict, cfg: OrbConfig) -> str | None:
    """Mismo periodo con las dos fuentes: ¿dan las mismas operaciones?"""
    files = [f for f in manifest[name] if (data_dir / f[0]).exists()]
    if len(files) < 2:
        return None
    runs = []
    for fname, factor, _, _ in files[:2]:
        days = build_days(name, read_m1(data_dir / fname, factor, None, None, _window(name)))
        runs.append((fname, {t.d: t for t in backtest_orb(days, cfg).trades}))
    (fa, a), (fb, b) = runs
    common = sorted(set(a) & set(b))
    if len(common) < 20:
        return f"  solape {fa} / {fb}: solo {len(common)} días comunes con operación"
    same = sum(a[d].side == b[d].side for d in common)
    ra, rb = [a[d].r for d in common], [b[d].r for d in common]
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    corr = cov / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return (f"  solape {fa} / {fb} ({common[0]}..{common[-1]}): {len(common)} días con operación en ambas, "
            f"mismo lado {same / len(common) * 100:.0f}%, correlación de R {corr:.2f}, "
            f"R medio {ma:+.3f} / {mb:+.3f}; solo en una: {len(set(a) ^ set(b))}")


def run_market(name: str, days: list[Day], sources: list[dict], mc_sims: int, data_dir: Path, manifest: dict) -> dict:
    cfg = config_for(name)
    print(f"\n=== {name} ===")
    for s in sources:
        print(f"  fuente {s['file']}: " + ("NO ENCONTRADO" if s.get("missing") else
                                          f"{s['from']}..{s['to']}, {s['days']} días"))
    print(f"  spread mediano en la entrada: {entry_spread_median(days, cfg, until=SEEN_FROM):.2f} antes de "
          f"{SEEN_FROM}, {entry_spread_median(days, cfg, since=SEEN_FROM):.2f} después")
    ov = overlap_check(name, data_dir, manifest, cfg)
    if ov:
        print(ov)
    r1, r2 = backtest_orb(days, cfg), backtest_orb(days, replace(cfg, cost_mult=2.0))
    print(f"  completo, costes normales: {summary(r1)}")
    print(f"  completo, costes al doble: {summary(r2)}")
    for label, a, b in (("antes de " + SEEN_FROM, None, SEEN_FROM), ("desde " + SEEN_FROM, SEEN_FROM, None)):
        sub = [d for d in days if (not a or d.d >= a) and (not b or d.d < b)]
        if len(sub) > 60:
            print(f"  {label}, x1: {summary(backtest_orb(sub, cfg))}")
            print(f"  {label}, x2: {summary(backtest_orb(sub, replace(cfg, cost_mult=2.0)))}")
    print("  por años (costes normales; R medio al doble):")
    print("\n".join(by_year(r1, r2)))
    longs, shorts = [t for t in r1.trades if t.side == 1], [t for t in r1.trades if t.side == -1]
    print(f"  largos {trade_stats(longs)['mean_r']:+.3f} R ({len(longs)}), cortos "
          f"{trade_stats(shorts)['mean_r']:+.3f} R ({len(shorts)}), stops {sum(t.reason == 'SL' for t in r1.trades) / max(len(r1.trades), 1) * 100:.0f}%")
    wf_out = {}
    for label, mult in (("x1", 1.0), ("x2", 2.0)):
        ws = walk_forward(days, backtest_orb, replace(cfg, cost_mult=mult), orb_grid())["windows"]
        pos = sum(metrics(w["fixed"].equity)["total"] > 0 for w in ws)
        fixed, chosen = (metrics(chain([w[k] for w in ws], cfg.capital)) for k in ("fixed", "chosen"))
        wf_out[label] = {"windows": len(ws), "fixed_pos": pos, "fixed": fixed["total"], "chosen": chosen["total"]}
        print(f"  walk-forward {label}: {len(ws)} ventanas, fija positiva en {pos}; encadenado fija "
              f"{_pct(fixed['total'])} (caída {_pct(fixed['max_drawdown'])}), reoptimizada {_pct(chosen['total'])}")
        if label == "x1":
            for w in ws:
                print(f"    {w['from']}..{w['to']} fija {_pct(metrics(w['fixed'].equity)['total'])} | "
                      f"elegido {w['params']} {_pct(metrics(w['chosen'].equity)['total'])}")
    if mc_sims:
        for label, r in (("x1", r1), ("x2", r2)):
            mc = monte_carlo(daily_returns(r, cfg.capital), mc_sims)
            print(f"  Monte Carlo FTMO {label}: P(pass) {mc['p_pass'] * 100:.1f}% | P(fail) {mc['p_fail'] * 100:.1f}% "
                  f"| mediana {mc['days_p50']} días")
    return {"r1": r1, "r2": r2, "cfg": cfg, "wf": wf_out}


def pooled(results: dict[str, dict], mc_sims: int) -> None:
    print("\n=== Conjunto ===")
    names = list(results)
    for label, key in (("x1", "r1"), ("x2", "r2")):
        tr = [t for n in names for t in results[n][key].trades]
        new = [t for n in names for t in results[n][key].trades if n != "US100" or t.d < SEEN_FROM]
        a, b = trade_stats(tr), trade_stats(new)
        print(f"  todas las operaciones {label}: {a['trades']} ops, R medio {a['mean_r']:+.3f} (t {a['t']:.1f}) | "
              f"sin el periodo ya visto de US100: {b['trades']} ops, R medio {b['mean_r']:+.3f} (t {b['t']:.1f})")
    years = {}
    for n in names:
        for t in results[n]["r1"].trades:
            years.setdefault((n, t.d[:4]), []).append(t.r)
    pos = sum(sum(v) > 0 for v in years.values())
    print(f"  años-mercado con R medio > 0 (x1): {pos} de {len(years)} ({pos / len(years) * 100:.0f}%)")
    # Correlación de retornos diarios en los días comunes
    rets = {}
    for n in names:
        r = results[n]["r1"]
        eq = [r.equity[0]] + r.equity
        rets[n] = {d: eq[i + 1] / eq[i] - 1 for i, d in enumerate(r.dates)}
    print("  correlación de retornos diarios:")
    for i, a in enumerate(names):
        cells = []
        for b in names[i + 1:]:
            common = [d for d in rets[a] if d in rets[b] and (rets[a][d] or rets[b][d])]
            if len(common) > 30:
                xa, xb = [rets[a][d] for d in common], [rets[b][d] for d in common]
                ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
                c = sum((x - ma) * (y - mb) for x, y in zip(xa, xb)) / math.sqrt(
                    sum((x - ma) ** 2 for x in xa) * sum((y - mb) ** 2 for y in xb))
                cells.append(f"{b} {c:.2f}")
        if cells:
            print(f"    {a}: " + ", ".join(cells))
    # Cartera: cada mercado al riesgo indicado / número de mercados, días comunes del calendario de US100
    if "US100" in names and mc_sims:
        all_days = sorted(set().union(*(rets[n] for n in names)))
        common_from = max(results[n]["r1"].dates[0] for n in names)
        port = [sum(rets[n].get(d, 0.0) for n in names) / len(names) * 100 for d in all_days if d >= common_from]
        mc = monte_carlo(port, mc_sims)
        eq = [100_000.0]
        for x in port:
            eq.append(eq[-1] * (1 + x / 100))
        m = metrics(eq)
        print(f"  cartera de los {len(names)} con el riesgo repartido (0.5%/{len(names)} cada uno) desde {common_from}: "
              f"total {_pct(m['total'])}, caída {_pct(m['max_drawdown'])}, Sharpe {m['sharpe']:.2f}; "
              f"Monte Carlo P(pass) {mc['p_pass'] * 100:.1f}%")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="ORB de US100 sin reajustar en otros índices y con más historia")
    ap.add_argument("--data-dir", required=True, help="carpeta con los CSV M1 (data/ de Prop Firm Challenges)")
    ap.add_argument("--manifest", help="JSON {mercado: [[fichero, factor_spread, desde, hasta], ...]}")
    ap.add_argument("--only", nargs="*", choices=list(MARKETS))
    ap.add_argument("--monte-carlo", type=int, default=2000, metavar="SIMS")
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text()) if a.manifest else MANIFEST
    data_dir = Path(a.data_dir)
    results = {}
    for name in a.only or list(MARKETS):
        days, sources = load_market(name, data_dir, manifest)
        if len(days) < 250:
            print(f"\n=== {name} === sin datos suficientes ({len(days)} días): {sources}")
            continue
        results[name] = run_market(name, days, sources, a.monte_carlo, data_dir, manifest)
    if len(results) > 1:
        pooled(results, a.monte_carlo)


if __name__ == "__main__":
    main()
