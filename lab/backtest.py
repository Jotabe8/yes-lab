"""Backtester diario, solo largo, sin dependencias externas.

Reglas para evitar sesgos (ver trading/research/A-estrategias-y-evidencia.md):
- La señal se calcula con el cierre del día t y se opera desde el día t+1 (sin mirar al futuro).
- Cada cambio de posición paga comisión + deslizamiento.
- La validación walk-forward elige parámetros en una ventana y los mide en la siguiente.

Uso:
    python -m lab.backtest spy --strategy sma --fast 50 --slow 200
    python -m lab.backtest btc --walk-forward
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
YEAR = {"acciones": 252, "forex": 252, "cripto": 365}


@dataclass
class Result:
    equity: list[float]
    buy_hold: list[float]
    position: list[int]
    trades: list[float] = field(default_factory=list)


def sma(values: list[float], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= n:
            total -= values[i - n]
        if i >= n - 1:
            out[i] = total / n
    return out


def signals(closes: list[float], strategy: str, fast: int = 50, slow: int = 200, look: int = 126) -> list[int]:
    n = len(closes)
    if strategy == "sma":
        f, s = sma(closes, fast), sma(closes, slow)
        return [1 if f[i] is not None and s[i] is not None and f[i] > s[i] else 0 for i in range(n)]
    if strategy == "mom":
        return [1 if i >= look and closes[i] / closes[i - look] - 1 > 0 else 0 for i in range(n)]
    raise ValueError(f"estrategia desconocida: {strategy}")


def run(closes: list[float], sig: list[int], cost_pct: float = 0.15, capital: float = 10_000) -> Result:
    """cost_pct = comisión + deslizamiento por lado, en %."""
    cost = cost_pct / 100
    eq, bh, pos, trades = [capital], [capital], [0], []
    e, entry = capital, None
    for i in range(1, len(closes)):
        want = sig[i - 1]
        if want != pos[-1]:
            e *= 1 - cost
            if want == 1:
                entry = closes[i - 1] * (1 + cost)
            elif entry is not None:
                trades.append(closes[i - 1] * (1 - cost) / entry - 1)
                entry = None
        if want == 1:
            e *= closes[i] / closes[i - 1]
        pos.append(want)
        eq.append(e)
        bh.append(capital * closes[i] / closes[0])
    if entry is not None:
        trades.append(closes[-1] / entry - 1)
    return Result(eq, bh, pos, trades)


def metrics(equity: list[float], year: int) -> dict[str, float]:
    n = len(equity)
    years = max((n - 1) / year, 1e-9)
    cagr = (equity[-1] / equity[0]) ** (1 / years) - 1
    peak, mdd, rets = equity[0], 0.0, []
    for i in range(1, n):
        peak = max(peak, equity[i])
        mdd = min(mdd, equity[i] / peak - 1)
        rets.append(equity[i] / equity[i - 1] - 1)
    mean = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1))
    return {"cagr": cagr, "max_drawdown": mdd, "sharpe": mean / sd * math.sqrt(year) if sd else 0.0,
            "total": equity[-1] / equity[0] - 1}


def walk_forward(closes: list[float], strategy: str, year: int, cost_pct: float,
                 train_years: int = 3, test_years: int = 1) -> dict:
    """Optimiza en `train_years`, mide en los `test_years` siguientes y avanza."""
    grid = ([{"fast": f, "slow": s} for f in (20, 50, 100) for s in (100, 150, 200) if f < s]
            if strategy == "sma" else [{"look": k} for k in (63, 126, 189, 252)])
    tr, te = train_years * year, test_years * year
    oos_equity, chosen = [1.0], []
    start = 0
    while start + tr + te <= len(closes):
        train = closes[start:start + tr]
        best = max(grid, key=lambda p: metrics(run(train, signals(train, strategy, **p), cost_pct).equity, year)["sharpe"])
        # la ventana de test incluye el calentamiento necesario para que las medias existan
        warm = max(best.get("slow", 0), best.get("look", 0))
        seg = closes[start + tr - warm:start + tr + te]
        res = run(seg, signals(seg, strategy, **best), cost_pct)
        tail = res.equity[warm:]
        for i in range(1, len(tail)):
            oos_equity.append(oos_equity[-1] * tail[i] / tail[i - 1])
        chosen.append(best)
        start += te
    if len(oos_equity) < 2:
        raise ValueError("serie demasiado corta para walk-forward")
    return {"windows": len(chosen), "params": chosen, "oos": metrics(oos_equity, year)}


def load(ident: str) -> tuple[list[float], int]:
    rows = json.loads((DATA_DIR / f"{ident}.json").read_text())
    index = json.loads((DATA_DIR / "index.json").read_text())
    market = next((s["market"] for s in index["series"] if s["id"] == ident), "acciones")
    return [r["c"] for r in rows], YEAR[market]


def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Backtest de una serie de docs/data")
    ap.add_argument("serie")
    ap.add_argument("--strategy", choices=["sma", "mom"], default="sma")
    ap.add_argument("--fast", type=int, default=50)
    ap.add_argument("--slow", type=int, default=200)
    ap.add_argument("--look", type=int, default=126)
    ap.add_argument("--cost", type=float, default=0.15, help="comisión + deslizamiento por lado, en %%")
    ap.add_argument("--walk-forward", action="store_true")
    a = ap.parse_args(argv)

    closes, year = load(a.serie)
    params = {"fast": a.fast, "slow": a.slow} if a.strategy == "sma" else {"look": a.look}
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        res = run(closes, signals(closes, a.strategy, **params), cost)
        s, b = metrics(res.equity, year), metrics(res.buy_hold, year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} (B&H {_pct(b['cagr'])}) | caída máx {_pct(s['max_drawdown'])} "
              f"(B&H {_pct(b['max_drawdown'])}) | Sharpe {s['sharpe']:.2f} (B&H {b['sharpe']:.2f}) | "
              f"{len(res.trades)} operaciones")
    if a.walk_forward:
        wf = walk_forward(closes, a.strategy, year, a.cost)
        o = wf["oos"]
        print(f"[walk-forward, {wf['windows']} ventanas fuera de muestra] CAGR {_pct(o['cagr'])} | "
              f"caída máx {_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f}")


if __name__ == "__main__":
    main()
