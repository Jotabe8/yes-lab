"""Estrategias intradía de Jorge en el Nasdaq 100 (US100.cash de FTMO), sin dependencias.

Port de los EAs del proyecto *Prop Firm Challenges*:

ORB_US100 v0.16 (configuración por defecto del EA)
- Rango de apertura: primeros 10 minutos desde las 16:30 del servidor (apertura cash USA).
- Dirección de la vela del rango: alcista → largo, bajista → corto; si el cuerpo es menor
  del 10% del rango (doji) no opera. Entrada a mercado al terminar el rango, como mucho
  5 minutos tarde.
- Stop al 15% del ATR(14) diario del día anterior. Sin objetivo: cierra a las 22:30.
- Riesgo 0.5% del tamaño nominal por operación, tope de exposición 6× la cuenta.
- Una operación al día; no opera en festivos de la bolsa USA.

VWAPMeanReversion_US100 v0.20 (configuración por defecto del EA)
- Velas M5. VWAP de la sesión desde las 16:30 con bandas de 1.5 desviaciones ponderadas
  por volumen de ticks.
- Largo si la vela cerrada acaba por debajo de la banda inferior, con ADX(14) < 30 y vela
  alcista; corto simétrico. Opera de 16:40 a 22:00 y cierra todo a las 22:45.
- Stop 1.5×ATR(14) de M5, objetivo el VWAP (beneficio/riesgo mínimo 0.5), salida tras 24 velas.
- Riesgo 0.5% por operación, máximo 3 operaciones al día, tope de beneficio diario 2%.

Datos: velas M1 del servidor de FTMO exportadas desde MetaTrader 5 (`python -m lab.us100
--export`, requiere el terminal abierto y el paquete MetaTrader5). Las horas son las del
servidor, que sigue el horario de verano de EE. UU.: la apertura cash cae siempre a las 16:30.

Costes: el spread registrado en la vela de entrada más 0.2 puntos de deslizamiento por
operación. FTMO no cobra comisión en índices; el parámetro existe por si cambia.
"Costes al doble" duplica spread, deslizamiento y comisión.

Uso:
    python -m lab.us100 --export                       # vuelca M1 desde MT5 a data/
    python -m lab.us100 --data RUTA.csv                # ORB y VWAP, costes normales y al doble
    python -m lab.us100 --data RUTA.csv --walk-forward --monte-carlo 5000
    python -m lab.us100 --data RUTA.csv --parity ORB_backtest_v16.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

from lab.nnfx import metrics, monte_carlo

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "US100_cash_M1_FTMO.csv"
POINT = 0.01          # US100.cash: 2 decimales
LOT_VALUE = 1.0       # USD por punto de índice y lote (contrato 1)
LOT_STEP = 0.01

# Festivos y cierres anticipados de la bolsa USA. 2024-2026 son los del EA; 2021-2023
# aplican la misma regla para poder usar todo el histórico.
US_HOLIDAYS = {
    "2021-09-06", "2021-11-25", "2021-11-26", "2021-12-24",
    "2022-01-17", "2022-02-21", "2022-04-15", "2022-05-30", "2022-06-20", "2022-07-04",
    "2022-09-05", "2022-11-24", "2022-11-25", "2022-12-26",
    "2023-01-02", "2023-01-16", "2023-02-20", "2023-04-07", "2023-05-29", "2023-06-19",
    "2023-07-03", "2023-07-04", "2023-09-04", "2023-11-23", "2023-11-24", "2023-12-25",
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19",
    "2024-07-03", "2024-07-04", "2024-09-02", "2024-11-28", "2024-11-29", "2024-12-24", "2024-12-25",
    "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
    "2025-07-03", "2025-07-04", "2025-09-01", "2025-11-27", "2025-11-28", "2025-12-24", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-11-26", "2026-11-27", "2026-12-24", "2026-12-25",
}


@dataclass(frozen=True)
class Bar:
    m: int          # minuto del día (hora del servidor)
    o: float
    h: float
    l: float
    c: float
    v: int          # volumen de ticks
    sp: int         # spread en puntos


@dataclass
class Day:
    d: str
    bars: list[Bar]
    atr: float | None = None      # ATR(14) diario del día anterior (iATR D1, desplazamiento 1)


@dataclass
class Trade:
    d: str
    side: int
    lots: float
    entry: float
    exit: float
    reason: str
    stop_dist: float
    risk_money: float
    pnl: float

    @property
    def r(self) -> float:
        return self.pnl / self.risk_money if self.risk_money else 0.0


@dataclass
class Result:
    dates: list[str]
    equity: list[float]
    trades: list[Trade] = field(default_factory=list)


# ── Datos ────────────────────────────────────────────────────────────────────

def load_m1(path: str | Path, since: str | None = None, until: str | None = None) -> list[Day]:
    """Lee el CSV M1 (time,open,high,low,close,tick_volume,spread) y lo agrupa por día del servidor."""
    days: dict[str, list[Bar]] = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            d, t = r["time"].split()
            days.setdefault(d, []).append(Bar(int(t[:2]) * 60 + int(t[3:5]), float(r["open"]), float(r["high"]),
                                              float(r["low"]), float(r["close"]), int(r["tick_volume"]), int(r["spread"])))
    # Antes de sep-2021 el servidor solo guarda velas diarias: se descartan los días sin M1.
    out = [Day(d, b) for d, b in sorted(days.items()) if len(b) >= 60]
    add_daily_atr(out)
    return [x for x in out if (since is None or x.d >= since) and (until is None or x.d < until)]


def add_daily_atr(days: list[Day], n: int = 14) -> None:
    """ATR(n) de las velas diarias hechas con las M1 (media simple del rango verdadero, como iATR)."""
    trs, prev_c = [], None
    for i, day in enumerate(days):
        h = max(b.h for b in day.bars)
        l = min(b.l for b in day.bars)
        trs.append(h - l if prev_c is None else max(h, prev_c) - min(l, prev_c))
        prev_c = day.bars[-1].c
        if i >= 1 and len(trs) - 1 >= n:
            day.atr = sum(trs[-1 - n:-1]) / n


# ── ORB ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrbConfig:
    or_minutes: int = 10
    min_body_pct: float = 10.0
    stop_mode: int = 1               # 0 = extremo opuesto del rango, 1 = % del ATR diario
    stop_atr_pct: float = 15.0
    target_r: float = 0.0            # 0 = sin objetivo
    session_start: int = 16 * 60 + 30
    trade_end: int = 22 * 60
    flat_time: int = 22 * 60 + 30
    max_entry_delay: int = 5
    max_notional_x: float = 6.0
    allow_long: bool = True
    allow_short: bool = True
    risk_pct: float = 0.5
    capital: float = 100_000.0
    cost_mult: float = 1.0
    slippage_pts: float = 0.2        # puntos de índice por operación (mitad a la entrada, mitad a la salida)
    commission: float = 0.0          # USD por lote, ida y vuelta


def lots_for(cfg_capital: float, risk_pct: float, stop_dist: float, price: float, max_notional_x: float) -> float:
    """CalcLots del EA: riesgo sobre el tamaño nominal, tope de exposición y redondeo hacia abajo al paso."""
    lots = cfg_capital * risk_pct / 100 / (stop_dist * LOT_VALUE)
    if max_notional_x > 0:
        lots = min(lots, cfg_capital * max_notional_x / (price * LOT_VALUE))
    lots = math.floor(lots / LOT_STEP + 1e-9) * LOT_STEP
    return round(lots, 2) if lots >= LOT_STEP else 0.0


def _exit_path(bars: list[Bar], k: int, side: int, stop: float, tp: float | None, spread: float,
               flat_time: int) -> tuple[float, str]:
    """Recorre las velas M1 desde la entrada. Precios bid; los cortos salen al ask (bid + spread).

    Si en la misma vela se tocan stop y objetivo, cuenta el stop (supuesto conservador).
    """
    for b in bars[k:]:
        if b.m >= flat_time:
            return (b.o if side == 1 else b.o + spread), "EA"
        if side == 1:
            if b.l <= stop:
                return min(stop, b.o), "SL"
            if tp is not None and b.h >= tp:
                return max(tp, b.o), "TP"
        else:
            if b.h + spread >= stop:
                return max(stop, b.o + spread), "SL"
            if tp is not None and b.l + spread <= tp:
                return min(tp, b.o + spread), "TP"
    last = bars[-1]
    return (last.c if side == 1 else last.c + spread), "EA"


def orb_signal(day: Day, cfg: OrbConfig) -> dict | None:
    """Evalúa el rango de apertura como EvaluateRange del EA. Devuelve la entrada o None."""
    if day.atr is None or day.d in US_HOLIDAYS:
        return None
    bars, ss = day.bars, cfg.session_start
    re_ = ss + cfg.or_minutes
    rb = [b for b in bars if ss <= b.m < re_]
    if not rb or rb[0].m > ss + 2:
        return None
    k = next((i for i, b in enumerate(bars) if b.m >= re_), None)
    if k is None or bars[k].m > re_ + cfg.max_entry_delay or bars[k].m > cfg.trade_end:
        return None
    hi, lo = max(b.h for b in rb), min(b.l for b in rb)
    rng, body = hi - lo, rb[-1].c - rb[0].o
    if rng <= 0 or abs(body) < rng * cfg.min_body_pct / 100:
        return None
    side = 1 if body > 0 else -1
    if (side == 1 and not cfg.allow_long) or (side == -1 and not cfg.allow_short):
        return None
    return {"k": k, "side": side, "hi": hi, "lo": lo}


def backtest_orb(days: list[Day], cfg: OrbConfig) -> Result:
    bal, dates, equity, trades = cfg.capital, [], [], []
    for day in days:
        sig = orb_signal(day, cfg)
        if sig:
            k, side, e = sig["k"], sig["side"], day.bars[sig["k"]]
            spread = e.sp * POINT * cfg.cost_mult
            slip = cfg.slippage_pts * cfg.cost_mult
            px = e.o + spread if side == 1 else e.o          # ask para largos, bid para cortos
            stop_dist = (day.atr * cfg.stop_atr_pct / 100 if cfg.stop_mode == 1
                         else (px - sig["lo"] if side == 1 else sig["hi"] - px))
            lots = lots_for(cfg.capital, cfg.risk_pct, stop_dist, px, cfg.max_notional_x) if stop_dist > 0 else 0
            if lots > 0:
                stop = px - side * stop_dist
                tp = px + side * cfg.target_r * stop_dist if cfg.target_r > 0 else None
                out, reason = _exit_path(day.bars, k, side, stop, tp, spread, cfg.flat_time)
                entry = px + side * slip / 2
                exit_ = out - side * slip / 2
                pnl = (exit_ - entry) * side * lots * LOT_VALUE - cfg.commission * cfg.cost_mult * lots
                trades.append(Trade(day.d, side, lots, entry, exit_, reason, stop_dist,
                                    lots * stop_dist * LOT_VALUE, pnl))
                bal += pnl
        dates.append(day.d)
        equity.append(bal)
    return Result(dates, equity, trades)


# ── VWAP reversión a la media ────────────────────────────────────────────────

@dataclass(frozen=True)
class VwapConfig:
    stop_atr: float = 1.5
    min_rr: float = 0.5
    max_bars_in_trade: int = 24
    entry_sigma: float = 1.5
    min_session_bars: int = 6
    use_adx: bool = True
    adx_max: float = 30.0
    adx_period: int = 14
    atr_period: int = 14
    reversal_candle: bool = True
    session_start: int = 16 * 60 + 30
    trade_start: int = 16 * 60 + 40
    trade_end: int = 22 * 60
    flat_time: int = 22 * 60 + 45
    daily_loss_pct: float = 3.0
    daily_profit_cap_pct: float = 2.0
    max_trades_day: int = 3
    risk_pct: float = 0.5
    capital: float = 100_000.0
    cost_mult: float = 1.0
    slippage_pts: float = 0.2
    commission: float = 0.0


def m5_bars(day: Day) -> list[tuple[Bar, int, int]]:
    """Velas M5 del día con los índices [i0, i1) de sus velas M1."""
    out, i = [], 0
    bars = day.bars
    while i < len(bars):
        start, j = bars[i].m // 5 * 5, i
        while j < len(bars) and bars[j].m // 5 * 5 == start:
            j += 1
        seg = bars[i:j]
        out.append((Bar(start, seg[0].o, max(b.h for b in seg), min(b.l for b in seg), seg[-1].c,
                        sum(b.v for b in seg), min(b.sp for b in seg)), i, j))
        i = j
    return out


def ema(values: list[float], n: int) -> list[float]:
    """ExponentialMA de MQL5: arranca con el primer valor, alfa 2/(n+1)."""
    a, out = 2 / (n + 1), []
    for i, v in enumerate(values):
        out.append(v if i == 0 else out[-1] + a * (v - out[-1]))
    return out


def adx_mt5(h: list[float], l: list[float], c: list[float], n: int) -> list[float]:
    """iADX de MetaTrader 5 (ADX.mq5): DI y ADX suavizados con media exponencial."""
    pdi, ndi = [0.0], [0.0]
    for i in range(1, len(c)):
        p, m = h[i] - h[i - 1], l[i - 1] - l[i]
        p, m = max(p, 0.0), max(m, 0.0)
        if p > m:
            m = 0.0
        elif m > p:
            p = 0.0
        else:
            p = m = 0.0
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        pdi.append(100 * p / tr if tr else 0.0)
        ndi.append(100 * m / tr if tr else 0.0)
    ps, ns = ema(pdi, n), ema(ndi, n)
    dx = [abs(a - b) / (a + b) * 100 if a + b else 0.0 for a, b in zip(ps, ns)]
    return ema(dx, n)


def atr_sma(h: list[float], l: list[float], c: list[float], n: int) -> list[float | None]:
    trs = [h[0] - l[0]] + [max(h[i], c[i - 1]) - min(l[i], c[i - 1]) for i in range(1, len(c))]
    out: list[float | None] = []
    s = 0.0
    for i, t in enumerate(trs):
        s += t
        if i >= n:
            s -= trs[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def backtest_vwap(days: list[Day], cfg: VwapConfig) -> Result:
    # Serie M5 continua (todas las horas) para ATR y ADX, como los indicadores del EA.
    per_day = [m5_bars(d) for d in days]
    flat = [b for bars in per_day for b, _, _ in bars]
    atr = atr_sma([b.h for b in flat], [b.l for b in flat], [b.c for b in flat], cfg.atr_period)
    adx = adx_mt5([b.h for b in flat], [b.l for b in flat], [b.c for b in flat], cfg.adx_period)

    bal, dates, equity, trades = cfg.capital, [], [], []
    g = 0                                                   # índice global de la vela M5
    for day, bars5 in zip(days, per_day):
        day_start, locked, n_today, pos = bal, False, 0, None
        m1 = day.bars
        for j, (b5, i0, i1) in enumerate(bars5):
            gi = g + j
            # --- al abrir la vela: gestión por tiempo, hora de cierre y señal con la vela anterior
            if pos and b5.m >= cfg.flat_time:
                bal += _close(pos, b5.o, cfg, trades, day.d, "EA")
                pos = None
            if pos and j - pos["j"] >= cfg.max_bars_in_trade:
                bal += _close(pos, b5.o, cfg, trades, day.d, "EA")
                pos = None
            if (not pos and not locked and cfg.trade_start <= b5.m < cfg.trade_end
                    and n_today < cfg.max_trades_day and j >= 1):
                sig = _vwap_signal(bars5, j, flat, gi, atr, adx, cfg)
                if sig:
                    side, vwap, stop_dist = sig
                    spread = b5.sp * POINT * cfg.cost_mult
                    px = b5.o + spread if side == 1 else b5.o
                    reward = (vwap - px) * side
                    lots = lots_for(cfg.capital, cfg.risk_pct, stop_dist, px, 0) if stop_dist > 0 else 0
                    if reward > 0 and (cfg.min_rr <= 0 or reward / stop_dist >= cfg.min_rr) and lots > 0:
                        pos = {"side": side, "px": px, "stop": px - side * stop_dist, "tp": vwap, "lots": lots,
                               "stop_dist": stop_dist, "spread": spread, "j": j}
                        n_today += 1
            # --- dentro de la vela: recorrer las M1
            for b in m1[i0:i1]:
                if b.m >= cfg.flat_time:
                    if pos:
                        bal += _close(pos, b.o, cfg, trades, day.d, "EA")
                        pos = None
                    break
                if not pos:
                    continue
                side, sp = pos["side"], pos["spread"]
                if side == 1 and b.l <= pos["stop"] or side == -1 and b.h + sp >= pos["stop"]:
                    px = min(pos["stop"], b.o) if side == 1 else max(pos["stop"], b.o + sp) - sp
                    bal += _close(pos, px, cfg, trades, day.d, "SL")
                    pos = None
                elif side == 1 and b.h >= pos["tp"] or side == -1 and b.l + sp <= pos["tp"]:
                    px = max(pos["tp"], b.o) if side == 1 else min(pos["tp"], b.o + sp) - sp
                    bal += _close(pos, px, cfg, trades, day.d, "TP")
                    pos = None
                else:
                    # frenos del día sobre la equity al cierre de la vela M1
                    open_pnl = ((b.c - pos["px"]) if side == 1 else (pos["px"] - b.c - sp)) * pos["lots"] * LOT_VALUE
                    eq = bal + open_pnl
                    if (cfg.daily_profit_cap_pct > 0 and eq >= day_start + cfg.daily_profit_cap_pct / 100 * cfg.capital
                            or eq <= day_start - cfg.daily_loss_pct / 100 * cfg.capital):
                        bal += _close(pos, b.c, cfg, trades, day.d, "EA")
                        pos, locked = None, True
                if not pos and (cfg.daily_profit_cap_pct > 0 and bal >= day_start + cfg.daily_profit_cap_pct / 100 * cfg.capital
                                or bal <= day_start - cfg.daily_loss_pct / 100 * cfg.capital):
                    locked = True
        if pos:                                              # sesión terminada antes de la hora de cierre
            bal += _close(pos, m1[-1].c, cfg, trades, day.d, "EA")
        g += len(bars5)
        dates.append(day.d)
        equity.append(bal)
    return Result(dates, equity, trades)


def _vwap_signal(bars5, j, flat, gi, atr, adx, cfg: VwapConfig):
    """CheckSignal del EA con la vela cerrada j-1."""
    sess = [b for b, _, _ in bars5[:j] if b.m >= cfg.session_start]
    if len(sess) < cfg.min_session_bars:
        return None
    sv = spv = 0.0
    for b in sess:
        v = max(b.v, 1)
        sv += v
        spv += v * (b.h + b.l + b.c) / 3
    vwap = spv / sv
    var = sum(max(b.v, 1) * ((b.h + b.l + b.c) / 3 - vwap) ** 2 for b in sess)
    sigma = math.sqrt(var / sv)
    a = atr[gi - 1]
    if sigma <= 0 or a is None:
        return None
    last = flat[gi - 1]
    if last.c < vwap - cfg.entry_sigma * sigma:
        side = 1
    elif last.c > vwap + cfg.entry_sigma * sigma:
        side = -1
    else:
        return None
    if cfg.use_adx and adx[gi - 1] >= cfg.adx_max:
        return None
    if cfg.reversal_candle and ((side == 1 and last.c <= last.o) or (side == -1 and last.c >= last.o)):
        return None
    return side, vwap, cfg.stop_atr * a


def _close(pos: dict, bid: float, cfg, trades: list[Trade], d: str, reason: str) -> float:
    """Cierra al precio bid dado (los cortos pagan el spread) con deslizamiento y comisión."""
    side, slip = pos["side"], cfg.slippage_pts * cfg.cost_mult
    out = bid if side == 1 else bid + pos["spread"]
    entry, exit_ = pos["px"] + side * slip / 2, out - side * slip / 2
    pnl = (exit_ - entry) * side * pos["lots"] * LOT_VALUE - cfg.commission * cfg.cost_mult * pos["lots"]
    trades.append(Trade(d, side, pos["lots"], entry, exit_, reason, pos["stop_dist"],
                        pos["lots"] * pos["stop_dist"] * LOT_VALUE, pnl))
    return pnl


# ── Estadísticas, walk-forward y Monte Carlo ─────────────────────────────────

def trade_stats(trades: list[Trade]) -> dict[str, float]:
    wins = sum(t.pnl for t in trades if t.pnl > 0)
    losses = -sum(t.pnl for t in trades if t.pnl < 0)
    rs = [t.r for t in trades]
    n = len(rs)
    mean = sum(rs) / n if n else 0.0
    sd = math.sqrt(sum((r - mean) ** 2 for r in rs) / (n - 1)) if n > 1 else 0.0
    return {"trades": n, "win_rate": sum(t.pnl > 0 for t in trades) / n if n else 0.0,
            "pf": wins / losses if losses else float("inf"), "mean_r": mean,
            "t": mean / sd * math.sqrt(n) if sd else 0.0}


def daily_returns(res: Result, capital: float) -> list[float]:
    """Retorno diario en % (incluye los días sin operación), como en el Monte Carlo del NNFX."""
    eq = [capital] + res.equity
    return [(eq[i] / eq[i - 1] - 1) * 100 for i in range(1, len(eq))]


def orb_grid() -> list[dict]:
    """Rejilla pequeña alrededor de la configuración del EA para el walk-forward."""
    return [{"or_minutes": m, "stop_atr_pct": s} for m in (5, 10, 15, 30) for s in (10, 15, 20, 30)]


def vwap_grid() -> list[dict]:
    return [{"entry_sigma": e, "stop_atr": s} for e in (1.0, 1.5, 2.0) for s in (1.0, 1.5, 2.0)]


def _shift_years(d: str, years: int) -> str:
    y, rest = int(d[:4]), d[4:]
    return f"{y + years}{rest}"


def walk_forward(days: list[Day], run, cfg, grid: list[dict], train_years: int = 3, test_years: int = 1) -> dict:
    """Elige parámetros por Sharpe en `train_years`, los mide en el año siguiente y avanza.

    Los indicadores diarios ya vienen calculados con todo el histórico previo, así que no
    hace falta calentamiento. La última ventana puede quedarse corta si no hay un año entero.
    """
    windows, start = [], days[0].d
    while True:
        mid, end = _shift_years(start, train_years), _shift_years(start, train_years + test_years)
        train = [d for d in days if start <= d.d < mid]
        test = [d for d in days if mid <= d.d < end]
        if len(test) < 120:
            break
        best = max(grid, key=lambda p: metrics(run(train, replace(cfg, **p)).equity)["sharpe"])
        fixed, chosen = run(test, cfg), run(test, replace(cfg, **best))
        windows.append({"from": test[0].d, "to": test[-1].d, "params": best,
                        "fixed": fixed, "chosen": chosen})
        start = _shift_years(start, test_years)
    return {"windows": windows}


def chain(results: list[Result], capital: float) -> list[float]:
    """Encadena las ventanas fuera de muestra (cada una arranca con `capital`) en una sola curva."""
    eq = [capital]
    for r in results:
        prev = capital
        for v in r.equity:
            eq.append(eq[-1] * v / prev)
            prev = v
    return eq


# ── Paridad con el tester de MT5 ─────────────────────────────────────────────

def parity(res: Result, tester_csv: str | Path) -> dict:
    """Compara día y lado con el CSV del EA (ORB_backtest_v16.csv, separador ';')."""
    with open(tester_csv, newline="", encoding="latin-1") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    ref = {r["Fecha"].replace(".", "-"): r for r in rows}
    mine = {t.d: t for t in res.trades if ref and min(ref) <= t.d <= max(ref)}
    both = sorted(set(ref) & set(mine))
    same_side = [d for d in both if (1 if ref[d]["Lado"] == "LONG" else -1) == mine[d].side]
    same_exit = [d for d in same_side if (ref[d]["Salida"] == "SL") == (mine[d].reason == "SL")]
    r_diff = [abs(float(ref[d]["R"]) - mine[d].r) for d in same_exit]
    return {"tester": len(ref), "port": len(mine), "common_days": len(both), "same_side": len(same_side),
            "same_exit": len(same_exit), "only_tester": sorted(set(ref) - set(mine)),
            "only_port": sorted(set(mine) - set(ref)),
            "median_abs_r_diff": sorted(r_diff)[len(r_diff) // 2] if r_diff else None}


# ── Exportación desde MT5 ────────────────────────────────────────────────────

def export_mt5(symbol: str, out: Path) -> int:  # pragma: no cover - requiere MetaTrader 5 abierto
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"No se pudo conectar con MetaTrader 5: {mt5.last_error()}")
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, dt.datetime(2000, 1, 1), dt.datetime.now() + dt.timedelta(days=1))
    if rates is None or not len(rates):
        raise SystemExit(f"{symbol}: sin datos ({mt5.last_error()})")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        f.write("time,open,high,low,close,tick_volume,spread\n")
        for x in rates:
            t = dt.datetime.fromtimestamp(int(x["time"]), dt.timezone.utc)
            f.write(f"{t:%Y-%m-%d %H:%M},{x['open']},{x['high']},{x['low']},{x['close']},{x['tick_volume']},{x['spread']}\n")
    return len(rates)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%"


def _line(label: str, res: Result) -> str:
    m, s = metrics(res.equity), trade_stats(res.trades)
    return (f"  {label:22} {res.dates[0]}..{res.dates[-1]} | total {_pct(m['total'])} | CAGR {_pct(m['cagr'])} "
            f"| caída máx {_pct(m['max_drawdown'])} | Sharpe {m['sharpe']:.2f} | PF {s['pf']:.2f} "
            f"| {s['trades']} ops, {s['win_rate'] * 100:.0f}% ganadoras | R medio {s['mean_r']:+.3f} (t {s['t']:.1f})")


STRATEGIES = {"orb": (backtest_orb, OrbConfig, orb_grid), "vwap": (backtest_vwap, VwapConfig, vwap_grid)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Backtest de ORB y VWAP en US100 con velas M1 de MT5")
    ap.add_argument("--data", default=str(DEFAULT_DATA), help="CSV M1 exportado de MT5")
    ap.add_argument("--export", action="store_true", help="exporta US100.cash M1 desde MT5 a --data")
    ap.add_argument("--symbol", default="US100.cash")
    ap.add_argument("--strategy", choices=["orb", "vwap", "all"], default="all")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--risk", type=float, default=0.5, help="riesgo por operación en %% del tamaño nominal")
    ap.add_argument("--walk-forward", action="store_true")
    ap.add_argument("--monte-carlo", type=int, metavar="SIMS")
    ap.add_argument("--parity", metavar="CSV", help="compara el ORB con el CSV del tester de MT5")
    a = ap.parse_args(argv)

    if a.export:
        n = export_mt5(a.symbol, Path(a.data))
        print(f"{n} velas M1 de {a.symbol} en {a.data}")
        return
    days = load_m1(a.data, a.since, a.until)
    names = ["orb", "vwap"] if a.strategy == "all" else [a.strategy]

    if a.parity:
        p = parity(backtest_orb(days, OrbConfig(risk_pct=a.risk, capital=10_000)), a.parity)
        print(f"[paridad ORB] tester {p['tester']} ops, port {p['port']} ops, días comunes {p['common_days']}, "
              f"mismo lado {p['same_side']}, misma salida (stop o no) {p['same_exit']}, "
              f"diferencia mediana de R {p['median_abs_r_diff']}")
        print(f"  solo en el tester: {p['only_tester']}\n  solo en el port: {p['only_port']}")
        return

    for name in names:
        run, Cfg, grid = STRATEGIES[name]
        cfg = Cfg(risk_pct=a.risk)
        print(f"\n=== {name.upper()} (riesgo {a.risk}%) ===")
        for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
            print(_line(label, run(days, replace(cfg, cost_mult=mult))))
        if a.monte_carlo:
            for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
                mc = monte_carlo(daily_returns(run(days, replace(cfg, cost_mult=mult)), cfg.capital), a.monte_carlo)
                print(f"  [Monte Carlo FTMO, {label}] P(pass) {mc['p_pass'] * 100:.1f}% | P(fail) "
                      f"{mc['p_fail'] * 100:.1f}% | mediana hasta pasar {mc['days_p50']} días | caída P95 {mc['dd_p95']:.1f}%")
        if a.walk_forward:
            for label, mult in (("costes normales", 1.0), ("costes al doble", 2.0)):
                wf = walk_forward(days, run, replace(cfg, cost_mult=mult), grid())
                ws = wf["windows"]
                print(f"  [walk-forward, {label}: 3 años de entrenamiento, 1 año fuera de muestra]")
                for w in ws:
                    print(f"    {w['from']}..{w['to']} elegido {w['params']} | fija "
                          f"{_pct(metrics(w['fixed'].equity)['total'])} | reoptimizada {_pct(metrics(w['chosen'].equity)['total'])}")
                for key in ("fixed", "chosen"):
                    eq = chain([w[key] for w in ws], cfg.capital)
                    m = metrics(eq)
                    print(f"    encadenado {'fija' if key == 'fixed' else 'reoptimizada'}: total {_pct(m['total'])} "
                          f"| caída máx {_pct(m['max_drawdown'])} | Sharpe {m['sharpe']:.2f}")


if __name__ == "__main__":
    main()
