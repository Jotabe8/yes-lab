"""Diario forward del EA ORB_US100: operaciones reales de la demo frente al backtest del mismo periodo.

Lee lo que exporta MetaTrader 5 (operaciones, órdenes, velas M1 y, si están, los logs del EA),
pasa el port del ORB (`lab.us100`) por los mismos días y compara día a día:

- si el EA operó cuando el backtest dice que tocaba, y por qué no cuando no lo hizo;
- el sentido, la hora y el precio de entrada y de salida;
- el deslizamiento frente al precio del modelo (en puntos de índice, positivo = en contra);
- el R de cada operación (beneficio neto / riesgo al stop) en la demo y en el backtest.

El informe sale en Markdown, pensado para repetirlo cada semana con todo el periodo forward.

Uso (en el PC con MetaTrader 5 abierto y la cuenta de la demo conectada):
    python -m lab.forward --export --raw diario_demo/raw            # vuelca operaciones, órdenes y M1
    python -m lab.forward --raw diario_demo/raw --since 2026-10-01 --out informes/forward/2026-10-26.md

Las horas son las del servidor de FTMO, igual que en `lab.us100`.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from lab.us100 import LOT_VALUE, POINT, US_HOLIDAYS, Day, OrbConfig, backtest_orb, load_m1

SYMBOL = "US100.cash"
LOG_KEYWORDS = ("doji", "descart", "skip", "no opera", "filtro", "filter", "news", "noticia", "fomc",
                "festivo", "holiday", "tarde", "late", "delay", "rango", "range", "error", "fail", "rechaz")


@dataclass
class LiveTrade:
    position: int
    d: str
    side: int               # 1 largo, -1 corto
    lots: float
    t_in: str               # HH:MM:SS del servidor
    t_out: str
    entry: float
    exit: float
    sl: float | None
    pnl: float              # beneficio + comisión + swap + comisiones extra
    commission: float
    exit_reason: str        # SL, TP, EA, manual…


# ── Lectura de lo exportado de MT5 ───────────────────────────────────────────

def _ts(v: str) -> dt.datetime:
    """Hora del servidor desde un epoch (MT5 lo devuelve así) o un texto 'AAAA-MM-DD HH:MM[:SS]'."""
    v = v.strip()
    if v.lstrip("-").isdigit():
        return dt.datetime.fromtimestamp(int(v), dt.timezone.utc).replace(tzinfo=None)
    return dt.datetime.fromisoformat(v.replace(".", "-", 2) if v[4:5] == "." else v)


def _f(r: dict, k: str) -> float:
    try:
        return float(r.get(k) or 0)
    except ValueError:
        return 0.0


DEAL_REASONS = {"0": "manual", "1": "móvil", "2": "web", "3": "EA", "4": "SL", "5": "TP", "6": "stop out"}


def load_live(deals_csv: str | Path, orders_csv: str | Path | None = None, symbol: str = SYMBOL,
              magic: int | None = None) -> list[LiveTrade]:
    """Agrupa los deals de MT5 por posición (entrada IN y salidas OUT) del símbolo indicado."""
    with open(deals_csv, newline="", encoding="utf-8-sig") as f:
        deals = [r for r in csv.DictReader(f) if r.get("symbol") == symbol]
    if magic is not None:
        deals = [r for r in deals if int(_f(r, "magic")) == magic]
    sl_by_order: dict[str, float] = {}
    if orders_csv and Path(orders_csv).exists():
        with open(orders_csv, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if _f(r, "sl"):
                    sl_by_order[r["ticket"]] = _f(r, "sl")
    by_pos: dict[str, list[dict]] = {}
    for r in deals:
        by_pos.setdefault(r["position_id"], []).append(r)
    out = []
    for pos, rs in by_pos.items():
        rs.sort(key=lambda r: int(_f(r, "time_msc")) or int(_f(r, "time")))
        ins = [r for r in rs if r["entry"] == "0"]
        outs = [r for r in rs if r["entry"] in ("1", "3")]
        if not ins or not outs:
            continue                      # posición abierta todavía
        i, o = ins[0], outs[-1]
        vol = sum(_f(r, "volume") for r in outs) or _f(i, "volume")
        exit_px = sum(_f(r, "price") * _f(r, "volume") for r in outs) / vol
        money = sum(_f(r, "profit") + _f(r, "commission") + _f(r, "swap") + _f(r, "fee") for r in rs)
        t_in, t_out = _ts(i["time"]), _ts(o["time"])
        out.append(LiveTrade(int(pos), t_in.date().isoformat(), 1 if i["type"] == "0" else -1, _f(i, "volume"),
                             f"{t_in:%H:%M:%S}", f"{t_out:%H:%M:%S}", _f(i, "price"), exit_px,
                             sl_by_order.get(i.get("order", "")), money,
                             sum(_f(r, "commission") + _f(r, "fee") for r in rs),
                             DEAL_REASONS.get(o.get("reason", ""), o.get("reason", "?"))))
    return sorted(out, key=lambda t: (t.d, t.t_in))


def normalize_m1(src: str | Path) -> Path:
    """Devuelve un CSV con el formato de `lab.us100.load_m1` (time de texto en hora del servidor)."""
    with open(src, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if rows and not rows[0]["time"].strip().isdigit() and "tick_volume" in rows[0]:
        return Path(src)
    tmp = Path(tempfile.mkstemp(suffix=".csv")[1])
    with open(tmp, "w", newline="") as f:
        f.write("time,open,high,low,close,tick_volume,spread\n")
        for r in rows:
            f.write(f"{_ts(r['time']):%Y-%m-%d %H:%M},{r['open']},{r['high']},{r['low']},{r['close']},"
                    f"{int(_f(r, 'tick_volume'))},{int(_f(r, 'spread'))}\n")
    return tmp


def point_value(info_json: str | Path | None) -> float:
    """USD por punto de índice y lote; del symbol_info exportado si está, si no el del port."""
    try:
        s = json.loads(Path(info_json).read_text()).get("symbol", {})
        return float(s["trade_tick_value"]) / float(s["trade_tick_size"])
    except (TypeError, OSError, KeyError, ValueError, ZeroDivisionError):
        return LOT_VALUE


def load_logs(log_dir: str | Path | None, ea_name: str = "ORB") -> dict[str, list[str]]:
    """Líneas del EA en los logs de expertos de MT5 (AAAAMMDD.log, UTF-16), por fecha del fichero."""
    out: dict[str, list[str]] = {}
    if not log_dir or not Path(log_dir).is_dir():
        return out
    for p in sorted(Path(log_dir).glob("*.log")):
        if not (p.stem.isdigit() and len(p.stem) == 8):
            continue
        raw = p.read_bytes()
        text = raw.decode("utf-16", errors="replace") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", errors="replace")
        d = f"{p.stem[:4]}-{p.stem[4:6]}-{p.stem[6:]}"
        for line in text.splitlines():
            if ea_name.lower() in line.lower():
                parts = line.split("\t")
                out.setdefault(d, []).append(" ".join(x.strip() for x in parts[2:] if x.strip()) or line.strip())
    return out


# ── Modelo ───────────────────────────────────────────────────────────────────

def model_reason(day: Day, cfg: OrbConfig) -> str:
    """Por qué el port no opera ese día (mismas comprobaciones que `orb_signal`)."""
    if day.d in US_HOLIDAYS:
        return "festivo USA"
    if day.atr is None:
        return "sin ATR (faltan días previos)"
    ss, re_ = cfg.session_start, cfg.session_start + cfg.or_minutes
    rb = [b for b in day.bars if ss <= b.m < re_]
    if not rb or rb[0].m > ss + 2:
        return "faltan velas en el rango"
    k = next((b for b in day.bars if b.m >= re_), None)
    if k is None or k.m > re_ + cfg.max_entry_delay:
        return "sin precio a la hora de entrada"
    hi, lo = max(b.h for b in rb), min(b.l for b in rb)
    body = rb[-1].c - rb[0].o
    if hi - lo <= 0 or abs(body) < (hi - lo) * cfg.min_body_pct / 100:
        return f"vela doji (cuerpo {abs(body) / (hi - lo) * 100 if hi > lo else 0:.0f}% del rango)"
    return "sin señal"


def _hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def compare(days: list[Day], live: list[LiveTrade], cfg: OrbConfig, pv: float = LOT_VALUE,
            logs: dict[str, list[str]] | None = None) -> list[dict]:
    """Una fila por día de mercado con lo que hizo la demo y lo que dice el modelo."""
    logs = logs or {}
    # Precios del modelo sin deslizamiento: el deslizamiento real se mide contra ellos.
    model = {t.d: t for t in backtest_orb(days, replace(cfg, slippage_pts=0.0)).trades}
    with_costs = {t.d: t for t in backtest_orb(days, cfg).trades}
    by_day: dict[str, list[LiveTrade]] = {}
    for t in live:
        by_day.setdefault(t.d, []).append(t)
    rows = []
    for day in days:
        m, mc, lv = model.get(day.d), with_costs.get(day.d), by_day.get(day.d, [])
        row = {"d": day.d, "model": m, "model_r": mc.r if mc else None, "live": lv,
               "reason": None if m else model_reason(day, cfg), "logs": logs.get(day.d, [])}
        if lv:
            t = lv[0]
            stop_dist = abs(t.entry - t.sl) if t.sl else (m.stop_dist if m else None)
            row["live_r"] = t.pnl / (t.lots * stop_dist * pv) if stop_dist else None
            row["stop_dist"] = stop_dist
            if m and m.side == t.side:
                row["slip_in"] = (t.entry - m.entry) * t.side
                if t.exit_reason == "SL" and t.sl:
                    row["slip_out"] = (t.sl - t.exit) * t.side       # contra el propio stop de la demo
                elif t.exit_reason == m.reason == "EA":
                    row["slip_out"] = (m.exit - t.exit) * t.side     # contra el cierre de las 22:30 del modelo
                row["stop_diff"] = (stop_dist - m.stop_dist) if stop_dist else None
        rows.append(row)
    return rows


def summary(rows: list[dict]) -> dict:
    model_days = [r for r in rows if r["model"]]
    live_days = [r for r in rows if r["live"]]
    both = [r for r in rows if r["model"] and r["live"]]
    same = [r for r in both if r["model"].side == r["live"][0].side]
    s_in = [r["slip_in"] for r in same if r.get("slip_in") is not None]
    s_out = [r["slip_out"] for r in same if r.get("slip_out") is not None]
    live_r = [r["live_r"] for r in live_days if r.get("live_r") is not None]
    model_r = [r["model_r"] for r in model_days]
    pair_r = [(r["live_r"], r["model_r"]) for r in same if r.get("live_r") is not None]
    return {
        "days": len(rows), "model_trades": len(model_days), "live_trades": sum(len(r["live"]) for r in rows),
        "both": len(both), "same_side": len(same),
        "missed": [r["d"] for r in model_days if not r["live"]],
        "extra": [r["d"] for r in live_days if not r["model"]],
        "slip_in_mean": statistics.mean(s_in) if s_in else None,
        "slip_in_max": max(s_in) if s_in else None,
        "slip_out_mean": statistics.mean(s_out) if s_out else None,
        "live_r_sum": sum(live_r), "live_r_mean": statistics.mean(live_r) if live_r else None,
        "model_r_sum": sum(model_r), "model_r_mean": statistics.mean(model_r) if model_r else None,
        "pair_diff_mean": statistics.mean(a - b for a, b in pair_r) if pair_r else None,
        "commission": sum(t.commission for r in live_days for t in r["live"]),
        "pnl": sum(t.pnl for r in live_days for t in r["live"]),
    }


# ── Informe ──────────────────────────────────────────────────────────────────

def _n(v: float | None, fmt: str = "+.2f") -> str:
    return "—" if v is None else format(v, fmt)


def _side(s: int) -> str:
    return "largo" if s == 1 else "corto"


def render(rows: list[dict], s: dict, since: str, until: str, cfg: OrbConfig) -> str:
    match = s["same_side"] / s["model_trades"] * 100 if s["model_trades"] else 0
    lines = [
        f"# Diario forward ORB_US100: demo frente a backtest ({since} a {until})",
        "",
        "Operaciones reales del EA en la demo de FTMO comparadas con el port del ORB (`lab/us100.py`) "
        "en los mismos días y con las mismas velas M1 del servidor. Simulado, sin dinero real. "
        "Deslizamiento en puntos de índice, positivo = en contra.",
        "",
        "## Resumen",
        "",
        "| | Demo | Backtest |",
        "| --- | --- | --- |",
        f"| Días de mercado | {s['days']} | {s['days']} |",
        f"| Operaciones | {s['live_trades']} | {s['model_trades']} |",
        f"| R total | {_n(s['live_r_sum'])} | {_n(s['model_r_sum'])} |",
        f"| R medio por operación | {_n(s['live_r_mean'])} | {_n(s['model_r_mean'])} |",
        "",
        f"- Coincidencia: {s['same_side']} de {s['model_trades']} operaciones del backtest ({match:.0f}%) "
        f"se abrieron en la demo el mismo día y en el mismo sentido.",
        f"- El EA no operó cuando el backtest sí: {len(s['missed'])} días ({', '.join(s['missed']) or 'ninguno'}).",
        f"- El EA operó cuando el backtest no: {len(s['extra'])} días ({', '.join(s['extra']) or 'ninguno'}).",
        f"- Deslizamiento de entrada: medio {_n(s['slip_in_mean'])} puntos, peor {_n(s['slip_in_max'])} "
        f"(el backtest supone {cfg.slippage_pts / 2:.2f} más el spread de la vela). "
        f"De salida: medio {_n(s['slip_out_mean'])}.",
        f"- R de la demo menos R del backtest, en las operaciones comunes: {_n(s['pair_diff_mean'])} de media.",
        f"- Resultado neto de la demo {s['pnl']:+.2f}, del que comisiones {s['commission']:+.2f}.",
        "",
        "## Día a día",
        "",
        "| Día | Backtest | Demo | Entrada demo / modelo | Desl. entrada | Salida demo / modelo | Desl. salida | R demo | R backtest | Nota |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        m, lv = r["model"], r["live"]
        t = lv[0] if lv else None
        bt = f"{_side(m.side)} {m.reason}" if m else "no opera"
        demo = f"{_side(t.side)} {t.exit_reason}" + (f" (+{len(lv) - 1})" if len(lv) > 1 else "") if t else "no opera"
        ent = f"{t.t_in[:5]} {t.entry:.2f} / {m.entry:.2f}" if t and m else (f"{t.t_in[:5]} {t.entry:.2f}" if t else (f"{m.entry:.2f}" if m else ""))
        ext = f"{t.t_out[:5]} {t.exit:.2f} / {m.exit:.2f}" if t and m else (f"{t.t_out[:5]} {t.exit:.2f}" if t else (f"{m.exit:.2f}" if m else ""))
        note = []
        if m and not t:
            note.append("el EA no abrió")
        if t and not m:
            note.append(f"el modelo no opera: {r['reason']}")
        if not m and not t:
            note.append(r["reason"])
        if m and t and m.side != t.side:
            note.append("sentido contrario")
        if r.get("stop_diff") and abs(r["stop_diff"]) > 0.5:
            note.append(f"stop {r['stop_dist']:.1f} frente a {m.stop_dist:.1f}")
        if (m and not t) or (t and not m):
            hits = [x for x in r["logs"] if any(k in x.lower() for k in LOG_KEYWORDS)][:2]
            if hits:
                note.append("log: " + " · ".join(h[:90] for h in hits))
        lines.append(f"| {r['d']} | {bt} | {demo} | {ent} | {_n(r.get('slip_in'))} | {ext} | {_n(r.get('slip_out'))} | "
                     f"{_n(r.get('live_r'))} | {_n(r['model_r'])} | {'; '.join(note).replace('|', '/')} |")
    lines += [
        "",
        "## Cómo leerlo",
        "",
        "- Lo importante es que la demo haga lo mismo que el backtest. Si coinciden los días y el "
        "sentido y el deslizamiento es pequeño, el R del backtest es una buena guía del R real.",
        "- Unas pocas semanas de R no dicen nada de la ventaja: con +0,19 R de media y un 70% de "
        "operaciones en stop, hacen falta cientos de operaciones para distinguirla del azar. "
        "Lo que sí se ve pronto es una ejecución distinta (días que faltan, deslizamiento alto, stops distintos).",
        f"- El modelo usa el riesgo del {cfg.risk_pct}% y los costes de `lab/us100.py`; no modela el filtro "
        "de noticias ni el cierre antes del FOMC de la build actual, así que esos días pueden salir como diferencias.",
        "",
    ]
    return "\n".join(lines)


# ── Exportación desde MT5 ────────────────────────────────────────────────────

def export_mt5(raw: Path, since: dt.datetime, symbol: str = SYMBOL) -> dict:  # pragma: no cover - requiere MT5
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"No se pudo conectar con MetaTrader 5: {mt5.last_error()}")
    raw.mkdir(parents=True, exist_ok=True)
    until = dt.datetime.now() + dt.timedelta(days=2)
    counts = {}
    for name, rows in (("deals", mt5.history_deals_get(since, until)), ("orders", mt5.history_orders_get(since, until))):
        rows = rows or ()
        with open(raw / f"{name}.csv", "w", newline="") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=list(rows[0]._asdict()))
                w.writeheader()
                w.writerows(r._asdict() for r in rows)
        counts[name] = len(rows)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, since - dt.timedelta(days=40), until)
    with open(raw / "us100_m1.csv", "w", newline="") as f:
        f.write("time,open,high,low,close,tick_volume,spread\n")
        for x in rates if rates is not None else ():
            t = dt.datetime.fromtimestamp(int(x["time"]), dt.timezone.utc)
            f.write(f"{t:%Y-%m-%d %H:%M},{x['open']},{x['high']},{x['low']},{x['close']},{x['tick_volume']},{x['spread']}\n")
    counts["m1"] = 0 if rates is None else len(rates)
    s, a = mt5.symbol_info(symbol), mt5.account_info()
    info = {"symbol": {k: getattr(s, k) for k in ("point", "digits", "trade_contract_size", "trade_tick_value",
                                                  "trade_tick_size", "volume_min", "volume_step")},
            "account": {k: getattr(a, k) for k in ("login", "balance", "equity", "currency", "leverage")}}
    (raw / "info.json").write_text(json.dumps(info, indent=2))
    mt5.shutdown()
    return counts


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Diario forward del ORB: demo de MT5 frente al backtest")
    ap.add_argument("--raw", default="diario_demo/raw", help="carpeta con deals.csv, orders.csv, us100_m1.csv, info.json y logs/")
    ap.add_argument("--export", action="store_true", help="vuelca operaciones, órdenes y velas M1 desde MT5 a --raw")
    ap.add_argument("--since", default="2026-10-01", help="primer día forward (hora del servidor)")
    ap.add_argument("--until", help="día siguiente al último a incluir (por defecto, hasta el final de los datos)")
    ap.add_argument("--symbol", default=SYMBOL)
    ap.add_argument("--magic", type=int, help="solo las operaciones con este número mágico")
    ap.add_argument("--risk", type=float, default=0.5)
    ap.add_argument("--capital", type=float, help="tamaño de la cuenta (por defecto, el balance de info.json o 100.000)")
    ap.add_argument("--out", help="escribe el informe en este fichero en vez de en pantalla")
    a = ap.parse_args(argv)
    raw = Path(a.raw)

    if a.export:
        c = export_mt5(raw, dt.datetime.fromisoformat(a.since) - dt.timedelta(days=7), a.symbol)
        print(f"{c['deals']} deals, {c['orders']} órdenes y {c['m1']} velas M1 en {raw}")
        return

    capital = a.capital
    if capital is None:
        try:
            capital = float(json.loads((raw / "info.json").read_text())["account"]["balance"])
        except (OSError, KeyError, ValueError):
            capital = 100_000.0
    cfg = OrbConfig(risk_pct=a.risk, capital=capital)
    days = [d for d in load_m1(normalize_m1(raw / "us100_m1.csv")) if d.d >= a.since and (a.until is None or d.d < a.until)]
    if not days:
        raise SystemExit("No hay velas M1 en el periodo pedido")
    live = [t for t in load_live(raw / "deals.csv", raw / "orders.csv", a.symbol, a.magic)
            if t.d >= a.since and (a.until is None or t.d < a.until)]
    rows = compare(days, live, cfg, point_value(raw / "info.json"), load_logs(raw / "logs"))
    report = render(rows, summary(rows), days[0].d, days[-1].d, cfg)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(report, encoding="utf-8")
        print(f"Informe en {a.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
