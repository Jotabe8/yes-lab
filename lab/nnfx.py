"""Estrategia NNFX de Jorge (portfolio de 5 pares validado en el proyecto FTMO), sin dependencias.

Port de nnfx_clasico_v1 (indicators.py + backtest.py, configuración "MT5 matched"):
- Baseline ALMA(50, sigma 6, offset 0.85); en EURAUD, Kijun(26).
- C1 ASH(9, 2) en modo RSI, C2 SSL(10), volumen tipo Hawkeye (la vela no puede ser "blanca").
- Entrada con regla de 7 velas, regla de una vela y "bridge too far" de 1 ATR.
- La señal se detecta al cierre de t y se ejecuta en la apertura de t+1.
- Posición única: SL 1×ATR, TP 1.5×ATR, y cierre al cierre de la vela si ASH o SSL
  se giran o el precio cruza la baseline.
- Riesgo 0.40% del balance por operación. Opera en largo y en corto.

Costes en pips como en costs.py del proyecto: spread (media entrada) + comisión por lote.

Uso:
    python -m lab.nnfx                      # portfolio de 5 pares, costes normales y al doble
    python -m lab.nnfx --walk-forward       # además, walk-forward anual
    python -m lab.nnfx --since 2020-01-01   # mismo periodo que los resultados previos
    python -m lab.nnfx --monte-carlo 5000   # probabilidad de pasar el challenge FTMO
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
YEAR = 252


@dataclass(frozen=True)
class Pair:
    baseline: str             # "alma" o "kijun"
    pip_size: float
    pip_value: float          # USD por pip y lote estándar
    commission: float         # USD por lote, ida y vuelta
    spread_pips: float


# Costes y stacks del portfolio validado (costs.py y run_hybrid_portfolio.py del proyecto)
PORTFOLIO = {
    "nzdusd": Pair("alma", 0.0001, 10.0, 7.0, 1.5),
    "usdchf": Pair("alma", 0.0001, 10.0, 7.0, 1.5),
    "usdjpy": Pair("alma", 0.01, 9.0, 7.0, 2.5),
    "euraud": Pair("kijun", 0.0001, 9.5, 7.0, 1.5),
    "gbpjpy": Pair("alma", 0.01, 9.0, 7.0, 1.5),
}


@dataclass(frozen=True)
class Config:
    baseline: str = "alma"
    alma_window: int = 50
    alma_sigma: float = 6.0
    alma_offset: float = 0.85
    kijun_period: int = 26
    atr_period: int = 14
    ash_length: int = 9
    ash_smooth: int = 2
    ssl_period: int = 10
    bridge_too_far_atr: float = 1.0
    seven_candle_rule: int = 7
    one_candle_rule: bool = True
    volume_filter: bool = True
    signal_exits: bool = True
    no_reentry_bars: int = 1
    sl_atr: float = 1.0
    tp_atr: float = 1.5
    risk_pct: float = 0.40
    capital: float = 100_000.0
    cost_mult: float = 1.0     # 2.0 = spread y comisión al doble


# ── Indicadores ──────────────────────────────────────────────────────────────

def rolling_mean(values: list[float | None], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(n - 1, len(values)):
        win = values[i - n + 1:i + 1]
        if all(v is not None for v in win):
            out[i] = sum(win) / n
    return out


def atr(h: list[float], l: list[float], c: list[float], n: int) -> list[float | None]:
    """Media simple del rango verdadero (atr_mt5 del proyecto)."""
    tr = [h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
                          for i in range(1, len(c))]
    return rolling_mean(tr, n)


def alma(c: list[float], window: int, sigma: float, offset: float) -> list[float | None]:
    m = math.floor(offset * (window - 1))
    s = window / sigma
    w = [math.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(window)]
    ws = sum(w)
    out: list[float | None] = [None] * len(c)
    for t in range(window - 1, len(c)):
        out[t] = sum(wi * v for wi, v in zip(w, c[t - window + 1:t + 1])) / ws
    return out


def kijun(h: list[float], l: list[float], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(h)
    for t in range(n - 1, len(h)):
        out[t] = (max(h[t - n + 1:t + 1]) + min(l[t - n + 1:t + 1])) / 2
    return out


def ash_signal(c: list[float], length: int, smooth: int) -> list[int]:
    """+1 si los toros dominan, -1 si los osos, 0 sin dato (ASH en modo RSI, medias simples)."""
    delta: list[float | None] = [None] + [c[i] - c[i - 1] for i in range(1, len(c))]
    bulls = [None if d is None else 0.5 * abs(d) + d for d in delta]
    bears = [None if d is None else 0.5 * abs(d) - d for d in delta]
    sb = rolling_mean(rolling_mean(bulls, length), smooth)
    sr = rolling_mean(rolling_mean(bears, length), smooth)
    out = []
    for b, r in zip(sb, sr):
        if b is None or r is None or b == r:
            out.append(0)
        else:
            out.append(1 if b > r else -1)
    return out


def ssl(h: list[float], l: list[float], c: list[float], n: int) -> list[int | None]:
    """Estado del canal SSL (+1/-1) usando las medias de máximos y mínimos de la vela anterior."""
    mh, ml = rolling_mean(h, n), rolling_mean(l, n)
    out: list[int | None] = [None] * len(c)
    for t in range(1, len(c)):
        hi, lo = mh[t - 1], ml[t - 1]
        if hi is None or lo is None:
            continue
        state = out[t - 1] or 0
        if c[t] > hi:
            state = 1
        if c[t] < lo:
            state = -1
        out[t] = state
    return out


def volume_ok(o: list[float], h: list[float], l: list[float], c: list[float]) -> list[bool]:
    """Vela con convicción (verde o roja en el Volume Type tipo Hawkeye), solo con OHLC."""
    out = [False]
    for t in range(1, len(c)):
        rng, mid = h[t] - l[t], (h[t] + l[t]) / 2
        red = c[t] < mid - rng / 6 and o[t] > c[t] and c[t] < l[t - 1]
        green = c[t] > mid + rng / 6 and o[t] < c[t] and c[t] > h[t - 1]
        out.append(red or green)
    return out


# ── Motor ────────────────────────────────────────────────────────────────────

@dataclass
class Trade:
    direction: int
    entry_i: int
    exit_i: int
    entry: float
    exit: float
    pnl: float
    reason: str


@dataclass
class Result:
    dates: list[str]
    equity: list[float]
    trades: list[Trade]


def backtest(bars: list[dict], cfg: Config, pair: Pair) -> Result:
    o = [b["o"] for b in bars]
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    n = len(c)

    base = (kijun(h, l, cfg.kijun_period) if cfg.baseline == "kijun"
            else alma(c, cfg.alma_window, cfg.alma_sigma, cfg.alma_offset))
    rng = atr(h, l, c, cfg.atr_period)
    c1 = ash_signal(c, cfg.ash_length, cfg.ash_smooth)
    c2 = ssl(h, l, c, cfg.ssl_period)
    vol = volume_ok(o, h, l, c)
    cross = [0] + [(1 if c1[i - 1] <= 0 < c1[i] else -1 if c1[i - 1] >= 0 > c1[i] else 0)
                   for i in range(1, n)]

    spread = pair.spread_pips * cfg.cost_mult * pair.pip_size
    commission = pair.commission * cfg.cost_mult

    def aligned(t: int, d: int) -> bool:
        if base[t] is None or rng[t] is None or c2[t] is None:
            return False
        if (d == 1 and not c[t] > base[t]) or (d == -1 and not c[t] < base[t]):
            return False
        if abs(c[t] - base[t]) > cfg.bridge_too_far_atr * rng[t]:
            return False
        if c2[t] != d:
            return False
        return vol[t] or not cfg.volume_filter

    balance = cfg.capital
    equity: list[float] = []
    trades: list[Trade] = []
    pos = None  # dict con la operación abierta
    last_c1 = {1: -10**9, -1: -10**9}
    last_stop = {1: -10**9, -1: -10**9}
    ocr: dict[int, int] = {}
    pending = None

    def close(t: int, price: float, reason: str) -> None:
        nonlocal balance, pos
        d, lots = pos["d"], pos["lots"]
        pnl = d * (price - pos["entry"]) / pair.pip_size * pair.pip_value * lots - commission * lots
        balance += pnl
        trades.append(Trade(d, pos["i"], t, pos["entry"], price, pnl, reason))
        if reason == "sl":
            last_stop[d] = t
        pos = None

    for t in range(n):
        # 1) ejecutar en la apertura la señal detectada al cierre anterior
        if pending is not None and pos is None:
            d, sig_i = pending
            pending = None
            a = rng[sig_i]
            entry = o[t] + d * spread / 2
            sl, tp = entry - d * cfg.sl_atr * a, entry + d * cfg.tp_atr * a
            sl_pips = abs(entry - sl) / pair.pip_size
            lots = round(balance * cfg.risk_pct / 100 / (sl_pips * pair.pip_value), 2) if sl_pips > 0 else 0.0
            pos = {"d": d, "i": t, "entry": entry, "sl": sl, "tp": tp, "lots": lots}
            last_c1[d] = -10**9

        if cross[t]:
            last_c1[cross[t]] = t

        # 2) gestionar la posición con el rango de la vela y salir por señal al cierre
        if pos is not None:
            d = pos["d"]
            if (d == 1 and l[t] <= pos["sl"]) or (d == -1 and h[t] >= pos["sl"]):
                close(t, pos["sl"], "sl")
            elif (d == 1 and h[t] >= pos["tp"]) or (d == -1 and l[t] <= pos["tp"]):
                close(t, pos["tp"], "tp")
            elif cfg.signal_exits:
                if c1[t] == -d:
                    close(t, c[t], "c1")
                elif (c2[t] or 0) == -d:
                    close(t, c[t], "ssl")
                elif base[t] is not None and d * (c[t] - base[t]) < 0:
                    close(t, c[t], "baseline")

        # 3) buscar señal nueva al cierre de t
        if pos is None and pending is None:
            for d in (1, -1):
                since = t - last_c1[d]
                if since < 0 or since > cfg.seven_candle_rule or t - last_stop[d] < cfg.no_reentry_bars:
                    continue
                if not aligned(t, d):
                    if cfg.one_candle_rule and since == 0:
                        ocr[d] = t
                    continue
                pending = (d, t)
                break
            if pending is None:
                for d, i in list(ocr.items()):
                    if t - i == 1:
                        del ocr[d]
                        if t - last_c1[d] <= cfg.seven_candle_rule and aligned(t, d):
                            pending = (d, i)
                            break

        floating = 0.0
        if pos is not None:
            floating = pos["d"] * (c[t] - pos["entry"]) / pair.pip_size * pair.pip_value * pos["lots"]
        equity.append(balance + floating)

    if pos is not None:
        close(n - 1, c[-1], "fin")
        equity[-1] = balance
    return Result([b["d"] for b in bars], equity, trades)


# ── Métricas, portfolio y walk-forward ───────────────────────────────────────

def metrics(equity: list[float]) -> dict[str, float]:
    years = max((len(equity) - 1) / YEAR, 1e-9)
    peak, mdd, rets = equity[0], 0.0, []
    for i in range(1, len(equity)):
        peak = max(peak, equity[i])
        mdd = min(mdd, equity[i] / peak - 1)
        rets.append(equity[i] / equity[i - 1] - 1)
    mean = sum(rets) / max(len(rets), 1)
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1))
    return {"total": equity[-1] / equity[0] - 1, "cagr": (equity[-1] / equity[0]) ** (1 / years) - 1,
            "max_drawdown": mdd, "sharpe": mean / sd * math.sqrt(YEAR) if sd else 0.0}


def trade_stats(trades: list[Trade]) -> dict[str, float]:
    wins = sum(t.pnl for t in trades if t.pnl > 0)
    losses = -sum(t.pnl for t in trades if t.pnl < 0)
    return {"trades": len(trades), "win_rate": sum(t.pnl > 0 for t in trades) / len(trades) if trades else 0.0,
            "pf": wins / losses if losses else float("inf")}


def combine(results: dict[str, Result], capital: float) -> tuple[list[str], list[float]]:
    """Suma el P&L de cada par sobre un mismo capital, alineando por fecha (el último valor se arrastra)."""
    dates = sorted({d for r in results.values() for d in r.dates})
    eq = []
    last = {k: capital for k in results}
    maps = {k: dict(zip(r.dates, r.equity)) for k, r in results.items()}
    for d in dates:
        for k, m in maps.items():
            if d in m:
                last[k] = m[d]
        eq.append(capital + sum(v - capital for v in last.values()))
    return dates, eq


def buy_hold(bars: list[dict], capital: float) -> list[float]:
    return [capital * b["c"] / bars[0]["c"] for b in bars]


def grid(pair: Pair) -> list[dict]:
    """Rejilla pequeña alrededor de la configuración validada para el walk-forward."""
    key = "kijun_period" if pair.baseline == "kijun" else "alma_window"
    lens = (20, 26, 34) if pair.baseline == "kijun" else (30, 50, 70)
    return [{key: b, "ssl_period": s} for b in lens for s in (7, 10, 14)]


def walk_forward(bars: list[dict], pair: Pair, cfg: Config,
                 train_years: int = 3, test_years: int = 1, warmup: int = 120) -> dict:
    """Elige parámetros por Sharpe en `train_years`, los mide en el año siguiente y avanza.

    Cada ventana de test arranca con el capital inicial y un calentamiento previo de
    `warmup` velas para que los indicadores existan; el calentamiento no cuenta.
    """
    tr, te = train_years * YEAR, test_years * YEAR
    windows, start = [], warmup
    while start + tr + te <= len(bars):
        train = bars[start - warmup:start + tr]
        best = max(grid(pair), key=lambda p: metrics(backtest(train, replace(cfg, **p), pair).equity)["sharpe"])
        seg = bars[start + tr - warmup:start + tr + te]
        fixed = backtest(seg, cfg, pair)
        chosen = backtest(seg, replace(cfg, **best), pair)
        windows.append({
            "from": seg[warmup]["d"], "to": seg[-1]["d"], "params": best,
            "fixed": _slice(fixed, warmup), "chosen": _slice(chosen, warmup),
        })
        start += te
    return {"windows": windows}


def _slice(res: Result, warmup: int) -> dict:
    """Resultado de la parte fuera de muestra, re-basado al inicio del test."""
    eq = res.equity[warmup - 1:]
    trades = [t for t in res.trades if t.entry_i >= warmup]
    return {"equity": eq, "ret": eq[-1] / eq[0] - 1, "trades": len(trades), "dates": res.dates[warmup - 1:]}


def chain(windows: list[dict], key: str, capital: float) -> tuple[list[str], list[float]]:
    """Encadena las ventanas fuera de muestra en una sola curva."""
    dates, eq = [], [capital]
    for w in windows:
        seg = w[key]["equity"]
        for i in range(1, len(seg)):
            eq.append(eq[-1] * seg[i] / seg[i - 1])
        dates += w[key]["dates"][1:]
    return [windows[0][key]["dates"][0]] + dates if windows else [], eq


def daily_bars(rows: list[dict]) -> list[dict]:
    """Rehace las velas diarias de forex de Yahoo.

    En forex, Yahoo pone como cierre diario el precio del arranque de la sesión
    (casi igual a la apertura), así que el cuerpo de la vela sale vacío y la regla
    de volumen casi nunca se cumple. El cierre real de la sesión es la apertura de
    la vela siguiente: se usa esa, y la última vela, aún sin cerrar, se descarta.
    """
    rows = [r for r in rows if all(k in r for k in ("o", "h", "l", "c"))]
    out = []
    for r, nxt in zip(rows, rows[1:]):
        c = nxt["o"]
        out.append({"d": r["d"], "o": r["o"], "h": max(r["h"], r["o"], c), "l": min(r["l"], r["o"], c), "c": c})
    return out


def portfolio_daily_returns(results: dict[str, Result]) -> list[float]:
    """Retorno diario del portfolio en %: suma de los retornos diarios de cada par (ftmo_montecarlo.py)."""
    rets: dict[str, float] = {}
    for r in results.values():
        for i in range(1, len(r.equity)):
            rets[r.dates[i]] = rets.get(r.dates[i], 0.0) + (r.equity[i] / r.equity[i - 1] - 1) * 100
    return [rets[d] for d in sorted(rets)]


def ftmo_path(daily_pct: list[float], target: float = 10.0, max_dd: float = 10.0, daily_dd: float = 5.0) -> dict:
    """Una trayectoria del challenge con las reglas de ftmo_montecarlo.py del proyecto.

    Como allí, la caída total se mide desde el máximo alcanzado (más estricto que el
    límite estático de FTMO) y la diaria como pérdida del día respecto al balance.
    """
    bal = peak = 100.0
    worst = 0.0
    for day, r in enumerate(daily_pct, 1):
        bal *= 1 + r / 100
        if -r >= daily_dd:
            return {"result": "FAIL", "days": day, "dd": worst}
        peak = max(peak, bal)
        worst = max(worst, peak - bal)
        if worst >= max_dd:
            return {"result": "FAIL", "days": day, "dd": worst}
        if bal - 100 >= target:
            return {"result": "PASS", "days": day, "dd": worst}
    return {"result": "TIMEOUT", "days": len(daily_pct), "dd": worst}


def monte_carlo(daily_pct: list[float], sims: int = 5000, days: int = 500, seed: int = 42) -> dict:
    """Bootstrap con reemplazo de días reales, como bootstrap_simulate del proyecto."""
    rnd = __import__("random").Random(seed)
    out = [ftmo_path([rnd.choice(daily_pct) for _ in range(days)]) for _ in range(sims)]
    passed = sorted(o["days"] for o in out if o["result"] == "PASS")
    dds = sorted(o["dd"] for o in out)
    return {"p_pass": len(passed) / sims, "p_fail": sum(o["result"] == "FAIL" for o in out) / sims,
            "days_p50": passed[len(passed) // 2] if passed else None, "dd_p95": dds[int(0.95 * (sims - 1))]}


def load(ident: str, since: str | None = None) -> list[dict]:
    bars = daily_bars(json.loads((DATA_DIR / f"{ident}.json").read_text()))
    if not bars:
        raise ValueError(f"{ident}: la serie no tiene OHLC; ejecuta python -m lab.fetch --only {ident}")
    return [b for b in bars if since is None or b["d"] >= since]


def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%"


def run_portfolio(since: str | None, cost_mult: float, cfg: Config) -> dict:
    per, bh = {}, {}
    for ident, pair in PORTFOLIO.items():
        bars = load(ident, since)
        per[ident] = backtest(bars, replace(cfg, baseline=pair.baseline, cost_mult=cost_mult), pair)
        bh[ident] = Result([b["d"] for b in bars], buy_hold(bars, cfg.capital), [])
    return {"pairs": per, "portfolio": combine(per, cfg.capital), "buy_hold": combine(bh, cfg.capital), "bh_pairs": bh}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Backtest del portfolio NNFX de 5 pares")
    ap.add_argument("--since", help="fecha inicial AAAA-MM-DD (por defecto, toda la serie)")
    ap.add_argument("--risk", type=float, default=0.40, help="riesgo por operación en %% del balance")
    ap.add_argument("--walk-forward", action="store_true")
    ap.add_argument("--monte-carlo", type=int, metavar="SIMS", help="simula el challenge FTMO con SIMS trayectorias")
    a = ap.parse_args(argv)
    cfg = Config(risk_pct=a.risk)

    for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
        r = run_portfolio(a.since, mult, cfg)
        print(f"\n[{label}]")
        for ident, res in r["pairs"].items():
            m, s = metrics(res.equity), trade_stats(res.trades)
            b = metrics(r["bh_pairs"][ident].equity)
            print(f"  {ident.upper():7} {res.dates[0]}..{res.dates[-1]} | total {_pct(m['total'])} "
                  f"(B&H {_pct(b['total'])}) | caída máx {_pct(m['max_drawdown'])} | Sharpe {m['sharpe']:.2f} "
                  f"| PF {s['pf']:.2f} | {s['trades']} operaciones, {s['win_rate'] * 100:.0f}% ganadoras")
        m, b = metrics(r["portfolio"][1]), metrics(r["buy_hold"][1])
        print(f"  PORTFOLIO total {_pct(m['total'])} (B&H cesta {_pct(b['total'])}) | CAGR {_pct(m['cagr'])} "
              f"(B&H {_pct(b['cagr'])}) | caída máx {_pct(m['max_drawdown'])} (B&H {_pct(b['max_drawdown'])}) "
              f"| Sharpe {m['sharpe']:.2f} (B&H {b['sharpe']:.2f})")

    if a.monte_carlo:
        for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
            mc = monte_carlo(portfolio_daily_returns(run_portfolio(a.since, mult, cfg)["pairs"]), a.monte_carlo)
            print(f"\n[Monte Carlo FTMO, {label}, {a.monte_carlo} simulaciones de 500 días] P(pass) {mc['p_pass'] * 100:.1f}% "
                  f"| P(fail) {mc['p_fail'] * 100:.1f}% | mediana hasta pasar {mc['days_p50']} días "
                  f"| caída P95 {mc['dd_p95']:.1f}%")

    if a.walk_forward:
        for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
            print(f"\n[walk-forward, {label}: 3 años de entrenamiento, 1 año fuera de muestra]")
            fixed, chosen = {}, {}
            for ident, pair in PORTFOLIO.items():
                wf = walk_forward(load(ident, a.since), pair, replace(cfg, baseline=pair.baseline, cost_mult=mult))
                ws = wf["windows"]
                pos_f = sum(w["fixed"]["ret"] > 0 for w in ws)
                pos_c = sum(w["chosen"]["ret"] > 0 for w in ws)
                fixed[ident] = Result(*chain(ws, "fixed", cfg.capital), [])
                chosen[ident] = Result(*chain(ws, "chosen", cfg.capital), [])
                print(f"  {ident.upper():7} {len(ws)} ventanas | fija: {pos_f}/{len(ws)} positivas, "
                      f"total {_pct(metrics(fixed[ident].equity)['total'])} | reoptimizada: {pos_c}/{len(ws)} "
                      f"positivas, total {_pct(metrics(chosen[ident].equity)['total'])}")
            for name, res in (("fija", fixed), ("reoptimizada", chosen)):
                m = metrics(combine(res, cfg.capital)[1])
                print(f"  PORTFOLIO {name}: total {_pct(m['total'])} | CAGR {_pct(m['cagr'])} | "
                      f"caída máx {_pct(m['max_drawdown'])} | Sharpe {m['sharpe']:.2f}")


if __name__ == "__main__":
    main()
