"""Estrategias del informe semanal de investigación, probadas con el backtester diario.

Cada semana la rutina "Estrategias de trading semanal" elige una o dos estrategias del informe
(trading/research/semanal/ en los archivos del proyecto), las añade aquí y apunta los
resultados en DIARIO.md. Reutiliza `run`, `metrics` y `load` de lab/backtest.py, así que
aplica las mismas reglas: la señal del cierre de t se opera desde t+1, solo largo y cada
cambio de posición paga comisión más deslizamiento.

Estrategias:
- cambio-de-mes: invertido solo los últimos `antes` días hábiles del mes y los primeros
  `despues` del siguiente (McConnell & Xu, 2008). El resto del tiempo, en liquidez sin interés.
- vol-gestionada: exposición al activo = volatilidad objetivo / volatilidad realizada de los
  últimos `dias` días, con tope `tope` (1 = sin apalancamiento), revisada a fin de mes
  (Moreira & Muir, 2017). Cada cambio de peso paga el coste sobre la parte que cambia.
- rebalanceo: front-running del rebalanceo de fin de mes de los fondos mixtos (Harvey, Mazzoleni
  & Melone, 2025). A `dias` sesiones del fin de mes mira la rentabilidad del mes: si sube más
  del `umbral`, vende el índice hasta el cierre del mes (los fondos venderán acciones); si cae
  más del `umbral`, lo compra. El resto del tiempo, en liquidez. Usa solo el índice como proxy:
  el laboratorio no tiene serie de bonos.
- momentum-divisas: cartera de 6 divisas frente al dólar (EUR, GBP, AUD, NZD, JPY, CHF);
  a fin de mes compra las `k` que más han subido en `meses` meses y vende las `k` que menos
  (Menkhoff et al., 2012). Exposición bruta 1. Solo precio: no incluye el diferencial de tipos.
- fixing-fin-de-mes: cobertura de divisa de los inversores extranjeros en bolsa de EE. UU.
  (Melvin & Prins, 2015). Si el S&P 500 ha subido en el mes, quien tiene acciones de EE. UU.
  con la divisa cubierta tiene que vender más dólares en el fixing de Londres del último día
  hábil, y el dólar baja; si ha caído, sube. El penúltimo cierre del mes se compran las 6
  divisas frente al dólar (o se venden) con exposición bruta 1, y se cierra el último día.
- subastas: ciclo de subastas del Tesoro de EE. UU. (Lou, Yan & Zhang, 2013). Los bonos bajan en
  las `antes` sesiones previas a cada subasta de los `plazos` elegidos y se recuperan en las
  `despues` siguientes. Corto antes y largo después; con --filtro, largo todo el tiempo salvo
  las sesiones previas (en liquidez). Fechas oficiales en docs/data/subastas.json.

Uso:
    python -m lab.estrategias cambio-de-mes spy
    python -m lab.estrategias cambio-de-mes spy --antes 1 --despues 3 --cost 0.05 --walk-forward
    python -m lab.estrategias vol-gestionada spy --cost 0.05 --walk-forward
    python -m lab.estrategias momentum-divisas fx --cost 0.02 --walk-forward
    python -m lab.estrategias rebalanceo spy --cost 0.05 --walk-forward
    python -m lab.estrategias fixing-fin-de-mes fx --cost 0.02 --walk-forward
    python -m lab.estrategias subastas tlt --plazos 10,30 --antes 5 --cost 0.05 --walk-forward
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


# --- Volatilidad gestionada -------------------------------------------------------------

def run_weights(closes: list[float], w: list[float], cost_pct: float, capital: float = 10_000) -> list[float]:
    """Curva de capital con exposición fraccional: w[t] (decidido al cierre de t) se aplica al día t+1.

    Cada cambio de peso paga `cost_pct` por lado sobre la fracción que cambia.
    """
    cost, eq, prev = cost_pct / 100, [capital], 0.0
    for i in range(1, len(closes)):
        e = eq[-1] * (1 - cost * abs(w[i - 1] - prev))
        eq.append(e * (1 + w[i - 1] * (closes[i] / closes[i - 1] - 1)))
        prev = w[i - 1]
    return eq


def vol_managed(dates: list[str], closes: list[float], year: int, objetivo: float = 0.12,
                dias: int = 21, tope: float = 1.0) -> list[float]:
    """Peso revisado el último día de cada mes con la volatilidad de los `dias` días previos."""
    _, last = month_ranks(dates)
    w, cur = [0.0] * len(closes), 0.0
    for i in range(len(closes)):
        if last[i] == 1 and i >= dias:
            rets = [closes[j] / closes[j - 1] - 1 for j in range(i - dias + 1, i + 1)]
            m = sum(rets) / dias
            vol = math.sqrt(sum((r - m) ** 2 for r in rets) / (dias - 1) * year)
            cur = min(tope, objetivo / vol) if vol else tope
        w[i] = cur
    return w


VOL_GRID = [{"objetivo": o, "dias": d} for o in (0.08, 0.12, 0.16, 0.20, 0.30) for d in (21, 63)]


def walk_forward_weights(dates, closes, year, cost_pct, build, grid, train_years=3, test_years=1) -> dict:
    """Walk-forward genérico para estrategias de pesos: `build(dates, closes, **p)` devuelve los pesos.

    La ventana de test arranca con el historial previo para que los pesos existan desde el primer día.
    """
    tr, te = train_years * year, test_years * year
    oos, chosen, start = [1.0], [], 0
    while start + tr + te <= len(closes):
        best = max(grid, key=lambda p: metrics(run_weights(closes[start:start + tr],
                                                           build(dates[start:start + tr], closes[start:start + tr], **p),
                                                           cost_pct), year)["sharpe"])
        w = build(dates[:start + tr + te], closes[:start + tr + te], **best)
        seg_c, seg_w = closes[start + tr - 1:start + tr + te], w[start + tr - 1:start + tr + te]
        eq = run_weights(seg_c, seg_w, cost_pct)
        for i in range(1, len(eq)):
            oos.append(oos[-1] * eq[i] / eq[i - 1])
        chosen.append(best)
        start += te
    if len(oos) < 2:
        raise ValueError("serie demasiado corta para walk-forward")
    return {"windows": len(chosen), "params": chosen, "oos": metrics(oos, year)}


# --- Rebalanceo de fin de mes -----------------------------------------------------------

def month_end_rebalance(dates: list[str], closes: list[float], dias: int = 3, umbral: float = 0.0,
                        bonos: list[float] | None = None) -> list[float]:
    """Pesos (+1, -1 o 0) decididos al cierre: se fijan cuando quedan `dias` sesiones para fin de mes.

    La señal del cierre de la sesión con last == dias + 1 se aplica a las `dias` últimas sesiones.
    Sin `bonos`, la señal es la rentabilidad del mes del índice. Con `bonos` (mismas fechas), es
    la desviación del peso en acciones de una cartera 60/40 rebalanceada a fin del mes anterior,
    como en el paper; entonces `umbral` se mide en puntos de peso (0.01 = 61% frente a 60%).
    """
    first, last = month_ranks(dates)
    w, cur = [0.0] * len(closes), 0.0
    for i in range(len(closes)):
        if last[i] == dias + 1 and i - first[i] >= 0:
            start = i - first[i]            # último cierre del mes anterior
            gs = closes[i] / closes[start]
            if bonos is None:
                dev = gs - 1
            else:
                gb = bonos[i] / bonos[start]
                dev = 0.6 * gs / (0.6 * gs + 0.4 * gb) - 0.6
            cur = -1.0 if dev > umbral else (1.0 if dev < -umbral else 0.0)
        elif last[i] == 1:
            cur = 0.0                       # cierra al terminar el mes
        w[i] = cur
    return w


REB_GRID = [{"dias": d, "umbral": u} for d in (1, 2, 3, 5) for u in (0.0, 0.02, 0.04)]
REB_GRID_6040 = [{"dias": d, "umbral": u} for d in (1, 2, 3, 5) for u in (0.0, 0.005, 0.01)]


# --- Momentum de divisas ----------------------------------------------------------------

FX_PAIRS = ("eurusd", "gbpusd", "nzdusd", "usdjpy", "usdchf", "euraud")


def fx_series() -> tuple[list[str], dict[str, list[float]]]:
    """Valor en dólares de 6 divisas, con fechas comunes y el cierre corregido de Yahoo (nnfx.daily_bars)."""
    from lab.nnfx import daily_bars

    raw = {p: {r["d"]: r["c"] for r in daily_bars(json.loads((DATA_DIR / f"{p}.json").read_text()))}
           for p in FX_PAIRS}
    dates = sorted(set.intersection(*(set(v) for v in raw.values())))
    usd = {
        "EUR": [raw["eurusd"][d] for d in dates],
        "GBP": [raw["gbpusd"][d] for d in dates],
        "NZD": [raw["nzdusd"][d] for d in dates],
        "JPY": [1 / raw["usdjpy"][d] for d in dates],
        "CHF": [1 / raw["usdchf"][d] for d in dates],
        "AUD": [raw["eurusd"][d] / raw["euraud"][d] for d in dates],
    }
    return dates, usd


def fx_momentum_weights(dates: list[str], prices: dict[str, list[float]], meses: int = 3, k: int = 2) -> list[dict[str, float]]:
    """Pesos decididos al cierre de cada día (cambian solo el último día del mes)."""
    _, last = month_ranks(dates)
    look = 21 * meses
    cur: dict[str, float] = {c: 0.0 for c in prices}
    out = []
    for i in range(len(dates)):
        if last[i] == 1 and i >= look:
            ranked = sorted(prices, key=lambda c: prices[c][i] / prices[c][i - look])
            cur = {c: 0.0 for c in prices}
            for c in ranked[-k:]:
                cur[c] = 0.5 / k
            for c in ranked[:k]:
                cur[c] = -0.5 / k
        out.append(dict(cur))
    return out


def run_portfolio(prices: dict[str, list[float]], w: list[dict[str, float]], cost_pct: float,
                  capital: float = 10_000) -> list[float]:
    """Curva de una cartera largo/corto: w[t] se aplica al día t+1 y cada cambio de peso paga costes."""
    cost, eq = cost_pct / 100, [capital]
    prev = {c: 0.0 for c in prices}
    n = len(next(iter(prices.values())))
    for i in range(1, n):
        turn = sum(abs(w[i - 1][c] - prev[c]) for c in prices)
        r = sum(w[i - 1][c] * (prices[c][i] / prices[c][i - 1] - 1) for c in prices)
        eq.append(eq[-1] * (1 - cost * turn) * (1 + r))
        prev = w[i - 1]
    return eq


def walk_forward_fx(dates, prices, year, cost_pct, train_years=3, test_years=1, k=2) -> dict:
    tr, te = train_years * year, test_years * year
    oos, chosen, start = [1.0], [], 0
    n = len(dates)
    sl = lambda a, b: {c: v[a:b] for c, v in prices.items()}
    while start + tr + te <= n:
        best = max((1, 3, 6, 12), key=lambda m: metrics(run_portfolio(
            sl(start, start + tr), fx_momentum_weights(dates[start:start + tr], sl(start, start + tr), m, k),
            cost_pct), year)["sharpe"])
        w = fx_momentum_weights(dates[:start + tr + te], sl(0, start + tr + te), best, k)
        eq = run_portfolio(sl(start + tr - 1, start + tr + te), w[start + tr - 1:start + tr + te], cost_pct)
        for i in range(1, len(eq)):
            oos.append(oos[-1] * eq[i] / eq[i - 1])
        chosen.append(best)
        start += te
    if len(oos) < 2:
        raise ValueError("serie demasiado corta para walk-forward")
    return {"windows": len(chosen), "params": chosen, "oos": metrics(oos, year)}


# --- Fixing de fin de mes ---------------------------------------------------------------

def month_end_fixing(dates: list[str], prices: dict[str, list[float]], equity: list[float],
                     umbral: float = 0.0) -> list[dict[str, float]]:
    """Pesos decididos al penúltimo cierre del mes (last == 2) y aplicados solo al último día.

    `equity` es el cierre del índice de EE. UU. alineado con `dates` (el último disponible en
    cada fecha). Si el mes va más de `umbral` en positivo, compra las divisas frente al dólar.
    """
    first, last = month_ranks(dates)
    n_cur, zero = len(prices), {c: 0.0 for c in prices}
    out = []
    for i in range(len(dates)):
        w = dict(zero)
        if last[i] == 2 and i - first[i] - 1 >= 0:
            mtd = equity[i] / equity[i - first[i] - 1] - 1   # desde el cierre del mes anterior
            if abs(mtd) > umbral:
                side = 1.0 if mtd > 0 else -1.0
                w = {c: side / n_cur for c in prices}
        out.append(w)
    return out


def aligned_equity(dates: list[str], ident: str = "spy") -> list[float]:
    """Cierre del índice en cada fecha de `dates`; si ese día no cotiza, el último anterior."""
    rows = json.loads((DATA_DIR / f"{ident}.json").read_text())
    out, j, cur = [], 0, rows[0]["c"]
    for d in dates:
        while j < len(rows) and rows[j]["d"] <= d:
            cur, j = rows[j]["c"], j + 1
        out.append(cur)
    return out


FIX_GRID = [{"umbral": u} for u in (0.0, 0.01, 0.02, 0.03)]


def walk_forward_portfolio(dates, prices, year, cost_pct, build, grid, train_years=3, test_years=1) -> dict:
    """Walk-forward para carteras: `build(dates, prices, **p)` devuelve los pesos por día."""
    tr, te = train_years * year, test_years * year
    oos, chosen, start = [1.0], [], 0
    sl = lambda a, b: {c: v[a:b] for c, v in prices.items()}
    while start + tr + te <= len(dates):
        best = max(grid, key=lambda p: metrics(run_portfolio(
            sl(start, start + tr), build(dates[start:start + tr], sl(start, start + tr), **p), cost_pct),
            year)["sharpe"])
        w = build(dates[:start + tr + te], sl(0, start + tr + te), **best)
        eq = run_portfolio(sl(start + tr - 1, start + tr + te), w[start + tr - 1:start + tr + te], cost_pct)
        for i in range(1, len(eq)):
            oos.append(oos[-1] * eq[i] / eq[i - 1])
        chosen.append(best)
        start += te
    if len(oos) < 2:
        raise ValueError("serie demasiado corta para walk-forward")
    return {"windows": len(chosen), "params": chosen, "oos": metrics(oos, year)}


# --- Ciclo de subastas del Tesoro -------------------------------------------------------

def auction_bucket(term: str) -> str:
    """Plazo nominal de una subasta: '9-Year 10-Month' (reapertura del 10 años) → '10'."""
    parts = term.replace("-Year", "").replace("-Month", "").split()
    years = int(parts[0]) + (int(parts[1]) / 12 if len(parts) > 1 else 0)
    for limit, name in ((27, "30"), (17, "20"), (8.5, "10"), (6, "7"), (4, "5"), (2.5, "3")):
        if years >= limit:
            return name
    return "2"


def load_auctions(plazos: tuple[str, ...]) -> set[str]:
    rows = json.loads((DATA_DIR / "subastas.json").read_text())
    return {r["d"] for r in rows if auction_bucket(r["plazo"]) in plazos}


def auction_cycle(dates: list[str], closes: list[float], subastas: set[str], antes: int = 5,
                  despues: int = 0, filtro: bool = False) -> list[float]:
    """Pesos decididos al cierre de t para el día t+1 según su distancia a la subasta más cercana.

    Las sesiones `antes` previas a una subasta van cortas (o en liquidez con `filtro`) y las
    `despues` siguientes, largas. Si ambas ventanas se solapan, manda la previa.
    """
    n = len(dates)
    held = [1.0 if filtro else 0.0] * n          # exposición deseada en cada sesión
    idx = [i for i, d in enumerate(dates) if d in subastas]
    for a in idx:
        for j in range(a + 1, min(n, a + despues + 1)):
            held[j] = 1.0
    for a in idx:
        for j in range(max(0, a - antes), a):
            held[j] = 0.0 if filtro else -1.0
    return held[1:] + [held[-1]]                 # w[t] se aplica a t+1


SUB_GRID = [{"antes": a, "despues": d} for a in (1, 2, 3, 4, 5) for d in (0, 3, 5)]
SUB_GRID_FILTRO = [{"antes": a, "despues": 0} for a in (1, 2, 3, 4, 5)]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Estrategias del informe semanal")
    ap.add_argument("estrategia", choices=["cambio-de-mes", "vol-gestionada", "momentum-divisas", "rebalanceo",
                                                 "subastas", "fixing-fin-de-mes"])
    ap.add_argument("serie", help="serie de docs/data (en momentum-divisas se ignora: usa los 6 pares)")
    ap.add_argument("--antes", type=int, default=1, help="sesiones finales del mes invertido")
    ap.add_argument("--despues", type=int, default=3, help="sesiones iniciales del mes siguiente invertido")
    ap.add_argument("--cost", type=float, default=0.15, help="comisión + deslizamiento por lado, en %%")
    ap.add_argument("--objetivo", type=float, default=0.12, help="vol-gestionada: volatilidad anual objetivo")
    ap.add_argument("--dias", type=int, default=21, help="vol-gestionada: días para medir la volatilidad")
    ap.add_argument("--tope", type=float, default=1.0, help="vol-gestionada: exposición máxima")
    ap.add_argument("--meses", type=int, default=3, help="momentum-divisas: meses de retorno para ordenar")
    ap.add_argument("--k", type=int, default=2, help="momentum-divisas: divisas compradas y vendidas")
    ap.add_argument("--umbral", type=float, default=0.0, help="rebalanceo: subida/caída mínima del mes")
    ap.add_argument("--bonos", help="rebalanceo: serie de bonos para la señal 60/40 (p. ej. tlt)")
    ap.add_argument("--plazos", default="10,30", help="subastas: plazos que cuentan (2,3,5,7,10,20,30)")
    ap.add_argument("--despues-sub", type=int, default=0, help="subastas: sesiones largas tras la subasta")
    ap.add_argument("--filtro", action="store_true", help="subastas: largo salvo antes de la subasta")
    ap.add_argument("--walk-forward", action="store_true")
    a = ap.parse_args(argv)

    if a.estrategia == "vol-gestionada":
        return _main_vol(a)
    if a.estrategia == "momentum-divisas":
        return _main_fx(a)
    if a.estrategia == "rebalanceo":
        return _main_reb(a)
    if a.estrategia == "subastas":
        return _main_sub(a)
    if a.estrategia == "fixing-fin-de-mes":
        return _main_fix(a)

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



def _main_vol(a) -> None:
    dates, closes, year = load_dated(a.serie)
    w = vol_managed(dates, closes, year, a.objetivo, a.dias, a.tope)
    bh = metrics([c / closes[0] for c in closes], year)
    print(f"{a.serie} {dates[0]} → {dates[-1]} | exposición media {sum(w) / len(w) * 100:.0f}% | "
          f"B&H CAGR {_pct(bh['cagr'])}, caída máx {_pct(bh['max_drawdown'])}, Sharpe {bh['sharpe']:.2f}")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        s = metrics(run_weights(closes, w, cost), year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} | caída máx {_pct(s['max_drawdown'])} | Sharpe {s['sharpe']:.2f}")
    if a.walk_forward:
        build = lambda d, c, **p: vol_managed(d, c, year, tope=a.tope, **p)
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_weights(dates, closes, year, cost, build, VOL_GRID)
            o = wf["oos"]
            params = ", ".join(f"{p['objetivo']:.0%}/{p['dias']}d" for p in wf["params"])
            print(f"[walk-forward, {label}, {wf['windows']} años] CAGR {_pct(o['cagr'])} | caída máx "
                  f"{_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | objetivo/días: {params}")
        # comprar y mantener en los mismos años fuera de muestra, para comparar
        start = 3 * year
        o = metrics([c / closes[start - 1] for c in closes[start - 1:start + wf["windows"] * year]], year)
        print(f"[B&H en los mismos años] CAGR {_pct(o['cagr'])} | caída máx {_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f}")


def _main_reb(a) -> None:
    dates, closes, year = load_dated(a.serie)
    bonos, grid = None, REB_GRID
    if a.bonos:
        bd, bc, _ = load_dated(a.bonos)
        common = sorted(set(dates) & set(bd))
        cmap, bmap = dict(zip(dates, closes)), dict(zip(bd, bc))
        dates, closes, bonos = common, [cmap[d] for d in common], [bmap[d] for d in common]
        grid = REB_GRID_6040
    dias = a.dias if a.dias != 21 else 3        # --dias por defecto es el de vol-gestionada
    w = month_end_rebalance(dates, closes, dias, a.umbral, bonos)
    trades = sum(1 for i in range(1, len(w)) if w[i] != 0 and w[i - 1] == 0)
    print(f"{a.serie} {dates[0]} → {dates[-1]} | últimas {dias} sesiones, umbral {a.umbral:.0%} | "
          f"{trades} operaciones, {sum(1 for x in w if x < 0)} días cortos y {sum(1 for x in w if x > 0)} largos")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        s = metrics(run_weights(closes, w, cost), year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} | caída máx {_pct(s['max_drawdown'])} | Sharpe {s['sharpe']:.2f}")
    if a.walk_forward:
        bmap = dict(zip(dates, bonos)) if bonos else None
        build = lambda d, c, **p: month_end_rebalance(d, c, bonos=[bmap[x] for x in d] if bmap else None, **p)
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_weights(dates, closes, year, cost, build, grid)
            o = wf["oos"]
            params = ", ".join(f"{p['dias']}d/{p['umbral']:.1%}" for p in wf["params"])
            print(f"[walk-forward, {label}, {wf['windows']} años] CAGR {_pct(o['cagr'])} | caída máx "
                  f"{_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | días/umbral: {params}")


def _main_sub(a) -> None:
    dates, closes, year = load_dated(a.serie)
    plazos = tuple(a.plazos.split(","))
    subastas = load_auctions(plazos)
    antes = a.antes if a.antes != 1 else 5       # --antes por defecto es el de cambio-de-mes
    w = auction_cycle(dates, closes, subastas, antes, a.despues_sub, a.filtro)
    n_sub = sum(1 for d in dates if d in subastas)
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    pre = [r for r, x in zip(rets, w[:-1]) if x == (0.0 if a.filtro else -1.0)]
    rest = [r for r, x in zip(rets, w[:-1]) if x != (0.0 if a.filtro else -1.0)]
    print(f"{a.serie} {dates[0]} → {dates[-1]} | {n_sub} días de subasta ({a.plazos} años) | "
          f"{len(pre)} sesiones previas: media {sum(pre) / len(pre) * 100:+.3f}% frente a "
          f"{sum(rest) / len(rest) * 100:+.3f}% el resto")
    bh = metrics([c / closes[0] for c in closes], year)
    print(f"[comprar y mantener] CAGR {_pct(bh['cagr'])} | caída máx {_pct(bh['max_drawdown'])} | Sharpe {bh['sharpe']:.2f}")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        s = metrics(run_weights(closes, w, cost), year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} | caída máx {_pct(s['max_drawdown'])} | Sharpe {s['sharpe']:.2f}")
    if a.walk_forward:
        build = lambda d, c, **p: auction_cycle(d, c, subastas, filtro=a.filtro, **p)
        grid = SUB_GRID_FILTRO if a.filtro else SUB_GRID
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_weights(dates, closes, year, cost, build, grid)
            o = wf["oos"]
            params = ", ".join(f"{p['antes']}/{p['despues']}" for p in wf["params"])
            print(f"[walk-forward, {label}, {wf['windows']} años] CAGR {_pct(o['cagr'])} | caída máx "
                  f"{_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | antes/después: {params}")
        start = 3 * year
        o = metrics([c / closes[start - 1] for c in closes[start - 1:start + wf["windows"] * year]], year)
        print(f"[B&H en los mismos años] CAGR {_pct(o['cagr'])} | caída máx {_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f}")


def _main_fx(a) -> None:
    dates, prices = fx_series()
    year = YEAR["forex"]
    w = fx_momentum_weights(dates, prices, a.meses, a.k)
    print(f"6 divisas frente al USD {dates[0]} → {dates[-1]} | {a.meses} meses, {a.k} largas y {a.k} cortas")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        s = metrics(run_portfolio(prices, w, cost), year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} | caída máx {_pct(s['max_drawdown'])} | Sharpe {s['sharpe']:.2f}")
    if a.walk_forward:
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_fx(dates, prices, year, cost, k=a.k)
            o = wf["oos"]
            print(f"[walk-forward, {label}, {wf['windows']} años] CAGR {_pct(o['cagr'])} | caída máx "
                  f"{_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | meses: {', '.join(map(str, wf['params']))}")


def _main_fix(a) -> None:
    dates, prices = fx_series()
    year = YEAR["forex"]
    equity = aligned_equity(dates, "spy")
    w = month_end_fixing(dates, prices, equity, a.umbral)
    rets = []
    for i in range(len(dates) - 1):
        if any(w[i].values()):
            rets.append(sum(w[i][c] * (prices[c][i + 1] / prices[c][i] - 1) for c in prices))
    mu = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / (len(rets) - 1))
    print(f"6 divisas frente al USD {dates[0]} → {dates[-1]} | señal: S&P 500 del mes, umbral {a.umbral:.0%} | "
          f"{len(rets)} operaciones, media {mu * 1e4:+.1f} pb por operación (t = {mu / sd * math.sqrt(len(rets)):.2f}), "
          f"aciertos {sum(r > 0 for r in rets) / len(rets):.0%}")
    for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
        s = metrics(run_portfolio(prices, w, cost), year)
        print(f"[{label}] CAGR {_pct(s['cagr'])} | caída máx {_pct(s['max_drawdown'])} | Sharpe {s['sharpe']:.2f}")
    if a.walk_forward:
        build = lambda d, p, **kw: month_end_fixing(d, p, aligned_equity(d, "spy"), **kw)
        for label, cost in (("costes normales", a.cost), ("costes al doble", a.cost * 2)):
            wf = walk_forward_portfolio(dates, prices, year, cost, build, FIX_GRID)
            o = wf["oos"]
            params = ", ".join(f"{p['umbral']:.0%}" for p in wf["params"])
            print(f"[walk-forward, {label}, {wf['windows']} años] CAGR {_pct(o['cagr'])} | caída máx "
                  f"{_pct(o['max_drawdown'])} | Sharpe {o['sharpe']:.2f} | umbral: {params}")


if __name__ == "__main__":
    main()
