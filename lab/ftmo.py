"""Monte Carlo del challenge de FTMO con sus reglas reales y criterio para apagar el EA ORB.

El Monte Carlo de `lab.nnfx` simplifica las reglas: caída total desde el máximo (más estricta
que la de FTMO), pérdida diaria con el cierre del día y sin días mínimos. Aquí se aplican las
del challenge 2-Step de FTMO (y el 1-Step como comparación):

- Pérdida diaria máxima: la equidad, contando la pérdida flotante, no puede caer más de un 5%
  del balance inicial por debajo del balance de medianoche. El EA abre una operación al día y
  la cierra a las 22:30, así que la peor equidad del día es el peor flotante de esa operación.
- Pérdida máxima: la equidad no puede bajar del 90% del balance inicial (fija en el 2-Step;
  en el 1-Step el suelo sube con el máximo balance de cierre).
- Días mínimos: 4 días con operaciones en cada fase. Sin límite de tiempo (se corta a 500 días).
- Noticias: en el challenge no hay restricción. En la cuenta FTMO estándar no se puede abrir ni
  cerrar en los 2 minutos de antes y después de una noticia de alto impacto (ver el informe).
- Freno del EA: `InpMaxLossPct = 8` deja de operar al perder un 8%; cuenta como intento perdido.
- El EA cierra antes del FOMC (`InpFomcClose`), así que el backtest de base lo hace también.

El tamaño de la operación se calcula sobre el tamaño nominal (fijo), así que el resultado de cada
día en % del balance inicial no depende del balance y los días se pueden sumar.

Uso:
    python -m lab.ftmo                       # Monte Carlo 2-Step y 1-Step, costes normales y al doble
    python -m lab.ftmo --sims 5000 --apagado # además, el criterio de apagado
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, replace

from lab.us100 import DEFAULT_DATA, OrbConfig, Result, backtest_orb, load_m1


@dataclass(frozen=True)
class Rules:
    name: str
    targets: tuple[float, ...] = (10.0, 5.0)   # objetivo de cada fase en % del balance inicial
    daily_loss: float = 5.0                    # % del balance inicial, desde el balance de medianoche
    max_loss: float = 10.0                     # % del balance inicial
    trailing: bool = False                     # el suelo sube con el máximo balance de cierre (1-Step)
    min_days: int = 4                          # días con operaciones por fase
    best_day: float | None = None              # el mejor día no puede pasar de este % de la suma de días positivos
    ea_brake: float | None = 8.0               # InpMaxLossPct del EA: deja de operar
    max_days: int = 500


TWO_STEP = Rules("FTMO 2-Step")
ONE_STEP = Rules("FTMO 1-Step", targets=(10.0,), daily_loss=3.0, trailing=True, best_day=50.0)


@dataclass(frozen=True)
class DayPnl:
    d: str
    pnl: float      # resultado cerrado del día en % del balance inicial
    low: float      # peor equidad del día respecto al balance de medianoche, en % (≤ 0)
    traded: bool


def day_pnls(res: Result, capital: float) -> list[DayPnl]:
    """Un registro por día de sesión, también los días sin operación."""
    by_day: dict[str, list] = {}
    for t in res.trades:
        by_day.setdefault(t.d, []).append(t)
    out = []
    for d in res.dates:
        ts = by_day.get(d, [])
        pnl, low, run = 0.0, 0.0, 0.0
        for t in ts:                       # el ORB abre una al día; si hubiera varias, van seguidas
            low = min(low, run + t.mae)
            run += t.pnl
        out.append(DayPnl(d, run / capital * 100, min(low, run) / capital * 100, bool(ts)))
    return out


def run_phase(days, target: float, rules: Rules) -> dict:
    """Recorre los días hasta pasar, suspender o agotar `max_days`. `days` es un iterador de DayPnl."""
    bal = peak = pos_sum = best = 0.0
    traded = 0
    for n, day in enumerate(days, 1):
        if n > rules.max_days:
            return {"result": "TIMEOUT", "days": n - 1}
        floor = (peak if rules.trailing else 0.0) - rules.max_loss
        if day.low <= -rules.daily_loss:
            return {"result": "FAIL_DIARIA", "days": n}
        if bal + day.low <= floor:
            return {"result": "FAIL_TOTAL", "days": n}
        if rules.ea_brake is not None and bal + day.low <= -rules.ea_brake:
            return {"result": "FRENO_EA", "days": n}
        bal += day.pnl
        peak = max(peak, bal)
        traded += day.traded
        if day.pnl > 0:
            pos_sum += day.pnl
            best = max(best, day.pnl)
        best_ok = rules.best_day is None or best <= pos_sum * rules.best_day / 100
        if bal >= target and traded >= rules.min_days and best_ok:
            return {"result": "PASS", "days": n}
    return {"result": "TIMEOUT", "days": rules.max_days}


def run_challenge(days, rules: Rules) -> dict:
    """Todas las fases seguidas sobre el mismo flujo de días. Devuelve la primera que no se pasa."""
    total = 0
    for i, target in enumerate(rules.targets):
        r = run_phase(days, target, rules)
        total += r["days"]
        if r["result"] != "PASS":
            return {"result": r["result"], "phase": i + 1, "days": total}
    return {"result": "PASS", "phase": len(rules.targets), "days": total}


def iid_stream(sample: list[DayPnl], rnd: random.Random):
    while True:
        yield rnd.choice(sample)


def block_stream(sample: list[DayPnl], rnd: random.Random, block: int = 20):
    """Bootstrap por bloques de días seguidos: conserva las rachas buenas y malas."""
    while True:
        i = rnd.randrange(len(sample) - block)
        yield from sample[i:i + block]


def monte_carlo(sample: list[DayPnl], rules: Rules, sims: int = 5000, method: str = "bloques",
                seed: int = 42) -> dict:
    rnd = random.Random(seed)
    if method == "historico":
        outs = []
        for i in range(len(sample)):
            r = run_challenge(iter(sample[i:]), replace(rules, max_days=len(sample)))
            if r["result"] != "TIMEOUT":   # el histórico se acabó antes de decidir: no cuenta
                outs.append(r)
    else:
        stream = block_stream if method == "bloques" else iid_stream
        outs = [run_challenge(stream(sample, rnd), rules) for _ in range(sims)]
    n = len(outs)
    count = lambda k: sum(o["result"] == k for o in outs) / n
    passed = sorted(o["days"] for o in outs if o["result"] == "PASS")
    phase1 = sum(o["result"] == "PASS" or o["phase"] > 1 for o in outs) / n
    return {"n": n, "p_pass": count("PASS"), "p_phase1": phase1, "p_fail_daily": count("FAIL_DIARIA"),
            "p_fail_total": count("FAIL_TOTAL"), "p_brake": count("FRENO_EA"), "p_timeout": count("TIMEOUT"),
            "days_p50": passed[len(passed) // 2] if passed else None,
            "days_p90": passed[int(0.9 * (len(passed) - 1))] if passed else None}


# ── Criterio de apagado ──────────────────────────────────────────────────────

def _max_streak(rs: list[float]) -> int:
    best = cur = 0
    for r in rs:
        cur = cur + 1 if r < 0 else 0
        best = max(best, cur)
    return best


def _max_dd(rs: list[float]) -> float:
    peak = cum = dd = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def _q(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]


def shutdown_bands(rs: list[float], horizon: int = 250, checkpoints: tuple[int, ...] = (20, 50, 100, 250),
                   sims: int = 10000, block: int = 10, seed: int = 7) -> dict:
    """Distribución de rachas, caídas y R acumulado si el EA sigue teniendo la ventaja del backtest.

    Bootstrap por bloques de `block` operaciones seguidas. `horizon` ≈ un año de operaciones.
    """
    rnd = random.Random(seed)
    streaks, dds, cums = [], [], {c: [] for c in checkpoints}
    for _ in range(sims):
        seq: list[float] = []
        while len(seq) < max(horizon, *checkpoints):
            i = rnd.randrange(len(rs) - block)
            seq.extend(rs[i:i + block])
        streaks.append(_max_streak(seq[:horizon]))
        dds.append(_max_dd(seq[:horizon]))
        for c in checkpoints:
            cums[c].append(sum(seq[:c]))
    return {
        "streak": {p: _q(streaks, p) for p in (0.5, 0.95, 0.99)},
        "dd": {p: _q(dds, p) for p in (0.5, 0.95, 0.99)},
        "cum": {c: {p: _q(v, p) for p in (0.01, 0.05, 0.5)} for c, v in cums.items()},
        "hist_streak": _max_streak(rs), "hist_dd": _max_dd(rs), "trades": len(rs),
        "mean_r": sum(rs) / len(rs),
    }


def red_flag(seq: list[float], bands: dict) -> int | None:
    """Operación en la que salta la alarma roja (racha o caída por encima del P99, o R acumulado bajo el P1)."""
    streak = cum = peak = 0.0
    for n, r in enumerate(seq, 1):
        streak = streak + 1 if r < 0 else 0
        cum += r
        peak = max(peak, cum)
        if streak >= bands["streak"][0.99] or peak - cum >= bands["dd"][0.99]:
            return n
        if n in bands["cum"] and cum < bands["cum"][n][0.01]:
            return n
    return None


def flag_rates(rs: list[float], bands: dict, shift: float = 0.0, length: int = 500, sims: int = 5000,
               block: int = 10, seed: int = 11) -> dict:
    """Con qué frecuencia salta la alarma roja si el R medio real es el del backtest más `shift`.

    shift = 0 mide las falsas alarmas; shift = −R medio, la detección de un EA sin ventaja.
    """
    rnd = random.Random(seed)
    hits = []
    for _ in range(sims):
        seq: list[float] = []
        while len(seq) < length:
            i = rnd.randrange(len(rs) - block)
            seq.extend(r + shift for r in rs[i:i + block])
        hits.append(red_flag(seq[:length], bands))
    return {n: sum(h is not None and h <= n for h in hits) / sims for n in (100, 250, 500)}


# ── CLI ──────────────────────────────────────────────────────────────────────

def _fmt(mc: dict) -> str:
    return (f"P(pass) {mc['p_pass'] * 100:5.1f}% | fase 1 {mc['p_phase1'] * 100:5.1f}% | pérdida diaria "
            f"{mc['p_fail_daily'] * 100:4.1f}% | pérdida total {mc['p_fail_total'] * 100:4.1f}% | freno EA "
            f"{mc['p_brake'] * 100:4.1f}% | sin decidir {mc['p_timeout'] * 100:4.1f}% | mediana {mc['days_p50']} "
            f"días (P90 {mc['days_p90']}) | n={mc['n']}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Monte Carlo del challenge de FTMO con las reglas reales")
    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--risk", type=float, default=0.5)
    ap.add_argument("--sims", type=int, default=5000)
    ap.add_argument("--apagado", action="store_true", help="bandas de rachas y caídas para apagar el EA")
    a = ap.parse_args(argv)

    days = load_m1(a.data, a.since, a.until)
    cfg = OrbConfig(risk_pct=a.risk, fomc_close=True)
    for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
        res = backtest_orb(days, replace(cfg, cost_mult=mult))
        sample = day_pnls(res, cfg.capital)
        worst = min(d.low for d in sample)
        print(f"\n=== ORB {a.risk}%, {label}, {sample[0].d}..{sample[-1].d} | peor día flotante {worst:.2f}% ===")
        for rules in (TWO_STEP, replace(TWO_STEP, name="FTMO 2-Step freno 9%", ea_brake=9.0),
                      replace(TWO_STEP, name="FTMO 2-Step sin freno", ea_brake=None), ONE_STEP):
            for method in ("iid", "bloques", "historico"):
                print(f"  {rules.name:22} {method:9} {_fmt(monte_carlo(sample, rules, a.sims, method))}")
        if a.apagado and mult == 1.0:
            rs = [t.r for t in res.trades]
            b = shutdown_bands(rs)
            print(f"\n  [apagado] {b['trades']} ops, R medio {b['mean_r']:+.3f}; histórico: racha máx {b['hist_streak']}, "
                  f"caída máx {b['hist_dd']:.1f} R")
            print(f"  racha de pérdidas en 250 ops: mediana {b['streak'][0.5]}, P95 {b['streak'][0.95]}, P99 {b['streak'][0.99]}")
            print(f"  caída máx en 250 ops (R): mediana {b['dd'][0.5]:.1f}, P95 {b['dd'][0.95]:.1f}, P99 {b['dd'][0.99]:.1f}")
            for c, q in b["cum"].items():
                print(f"  R acumulado tras {c:3} ops: P1 {q[0.01]:+.1f}, P5 {q[0.05]:+.1f}, mediana {q[0.5]:+.1f}")
            for label2, shift in (("con la ventaja del backtest (falsa alarma)", 0.0),
                                  ("con la mitad de la ventaja", -b["mean_r"] / 2),
                                  ("sin ventaja (R medio 0)", -b["mean_r"]),
                                  ("perdedor (R medio −0.10)", -b["mean_r"] - 0.10)):
                fr = flag_rates(rs, b, shift)
                print(f"  alarma roja {label2}: antes de 100 ops {fr[100] * 100:.0f}%, de 250 {fr[250] * 100:.0f}%, "
                      f"de 500 {fr[500] * 100:.0f}%")


if __name__ == "__main__":
    main()
