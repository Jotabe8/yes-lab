"""Estrategias del informe semanal de investigación, probadas con el backtester diario.

Cada semana la rutina "Estrategias de trading semanal" elige una o dos estrategias del informe
(trading/research/semanal/ en los archivos del proyecto), las añade aquí y apunta los
resultados en DIARIO.md. Reutiliza `run`, `metrics` y `load` de lab/backtest.py, así que
aplica las mismas reglas: la señal del cierre de t se opera desde t+1, solo largo y cada
cambio de posición paga comisión más deslizamiento.

Estrategias:
- cambio-de-mes: invertido solo los últimos `antes` días hábiles del mes y los primeros
  `despues` del siguiente (McConnell & Xu, 2008). El resto del tiempo, en liquidez sin interés.

Uso:
    python -m lab.estrategias cambio-de-mes spy
    python -m lab.estrategias cambio-de-mes spy --antes 1 --despues 3 --cost 0.05 --walk-forward
"""

from __future__ import annotations

import argparse
import json
import math

from lab.backtest import DATA_DIR, YEAR, _pct, metrics, run


def load_dated(ident: str) -> tuple[list[str], list[float], int]:
    rows = json.loads((DATA_DIR / f"{ident}.json").read_text())
    index = json.loads((DATA_DIR / "index.json").read_text())
    market = next((s["market"] for s in index["series"] if s["id"] == ident), "acciones")
    return [r["d"] for r in rows], [r["c"] for r in rows], YEAR[market]


def month_ranks(dates: list[str]) -> tuple[list[int], list[int]]:
    """Posición de cada sesión en su mes: desde el inicio (1 = primera) y desde el final (1 = última).

    El calendario de sesiones se conoce de antemano, así que saber que mañana es la última
    sesión del mes no es mirar al futuro. El último mes de la serie puede estar incompleto.
    """
    first, last = [0] * len(dates), [0] * len(dates)
    start = 0
    for i in range(1, len(dates) + 1):
        if i == len(dates) or dates[i][:7] != dates[start][:7]:
            n = i - start
            for k in range(n):
                first[start + k] = k + 1
                last[start + k] = n - k
            start = i
    return first, last


def turn_of_month(dates: list[str], antes: int = 1, despues: int = 3) -> list[int]:
    """Señal del cierre de t que da la posición del día t+1.

    Queremos ganar el retorno de las sesiones `antes` últimas del mes y `despues` primeras
    del siguiente, así que la señal de t vale 1 cuando la sesión t+1 cae en esa ventana.
    """
    first, last = month_ranks(dates)
    window = [1 if last[i] <= antes or first[i] <= despues else 0 for i in range(len(dates))]
    return window[1:] + [0]


def window_stats(closes: list[float], sig: list[int]) -> dict[str, float]:
    """Retorno medio diario dentro y fuera de la ventana y su estadístico t (Welch)."""
    inside, outside = [], []
    for i in range(1, len(closes)):
        (inside if sig[i - 1] else outside).append(closes[i] / closes[i - 1] - 1)

    def mv(xs: list[float]) -> tuple[float, float]:
        m = sum(xs) / len(xs)
        return m, sum((x - m) ** 2 for x in xs) / max(len(xs) - 1, 1)

    (mi, vi), (mo, vo) = mv(inside), mv(outside)
    t = (mi - mo) / math.sqrt(vi / len(inside) + vo / len(outside))
    return {"dentro": mi, "fuera": mo, "t": t, "exposicion": len(inside) / (len(closes) - 1)}


GRID = [{"antes": a, "despues": d} for a in (1, 2, 3, 4) for d in (1, 2, 3, 4)]


def walk_forward_tom(dates: list[str], closes: list[float], year: int, cost_pct: float,
                     train_years: int = 3, test_years: int = 1) -> dict:
    """Elige `antes` y `despues` por Sharpe en `train_years` y los mide en el año siguiente."""
    tr, te = train_years * year, test_years * year
    oos, chosen, start = [1.0], [], 0
    while start + tr + te <= len(closes):
        d_tr, c_tr = dates[start:start + tr], closes[start:start + tr]
        best = max(GRID, key=lambda p: metrics(run(c_tr, turn_of_month(d_tr, **p), cost_pct).equity, year)["sharpe"])
        # la señal del último día de entrenamiento decide la posición del primer día de test
        d_te, c_te = dates[start + tr - 1:start + tr + te], closes[start + tr - 1:start + tr + te]
        eq = run(c_te, turn_of_month(d_te, **best), cost_pct).equity
        for i in range(1, len(eq)):
            oos.append(oos[-1] * eq[i] / eq[i - 1])
        chosen.append(best)
        start += te
    if len(oos) < 2:
        raise ValueError("serie demasiado corta para walk-forward")
    return {"windows": len(chosen), "params": chosen, "oos": metrics(oos, year)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Estrategias del informe semanal")
    ap.add_argument("estrategia", choices=["cambio-de-mes"])
    ap.add_argument("serie")
    ap.add_argument("--antes", type=int, default=1, help="sesiones finales del mes invertido")
    ap.add_argument("--despues", type=int, default=3, help="sesiones iniciales del mes siguiente invertido")
    ap.add_argument("--cost", type=float, default=0.15, help="comisión + deslizamiento por lado, en %%")
    ap.add_argument("--walk-forward", action="store_true")
    a = ap.parse_args(argv)

    dates, closes, year = load_dated(a.serie)
    sig = turn_of_month(dates, a.antes, a.despues)
    w = window_stats(closes, sig)
    print(f"{a.serie} {dates[0]} → {dates[-1]} | invertido {w['exposicion'] * 100:.0f}% del tiempo | "
          f"retorno medio diario dentro {w['dentro'] * 100:+.3f}% vs fuera {w['fuera'] * 100:+.3f}% (t = {w['t']:.2f})")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        res = run(closes, sig, cost)
        s, b = metrics(res.equity, year), metrics(res.buy_hold, year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} (B&H {_pct(b['cagr'])}) | caída máx {_pct(s['max_drawdown'])} "
              f"(B&H {_pct(b['max_drawdown'])}) | Sharpe {s['sharpe']:.2f} (B&H {b['sharpe']:.2f}) | "
              f"{len(res.trades)} operaciones")
    if a.walk_forward:
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_tom(dates, closes, year, cost)
            o = wf["oos"]
            params = ", ".join(f"{p['antes']}/{p['despues']}" for p in wf["params"])
            print(f"[walk-forward, {label}, {wf['windows']} años fuera de muestra] CAGR {_pct(o['cagr'])} | "
                  f"caída máx {_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | antes/después: {params}")


if __name__ == "__main__":
    main()
