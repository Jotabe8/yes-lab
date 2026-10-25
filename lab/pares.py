"""Valor relativo (pares) en D1 con las reglas de informes/pares-preregistro.md.

Diferencial s = ln A − β·ln B (β por MCO en 120 cierres), z sobre los 60 diferenciales
anteriores. Señal al cierre de t, ejecución en la apertura de t+1. Entra con |z| > 2, sale con
|z| < 0,5, |z| > 4 o a los 20 días. Patas ponderadas por la inversa de su volatilidad y escaladas
a una volatilidad diaria del par del 1 % del capital. Resultados en % del capital, sin
capitalizar.

Los datos son los CSV D1 de Dukascopy del PC de Jorge (date,open,close,low,high,vol), que no
se suben al repositorio. Por defecto se leen de datos/d1/.

Uso:
    python -m lab.pares
    python -m lab.pares --datos datos/d1 --cost-mult 2
    python -m lab.pares --sensibilidad
    python -m lab.pares --beta-diario      # versión original, con el error de diseño
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DATOS = Path(__file__).resolve().parent.parent / "datos" / "d1"
CORTE = "2020-01-01"
FIN = "2025-12-31"

PARES = [
    ("US500/US100", "USA500IDXUSD", "USATECHIDXUSD"),
    ("US500/US30", "USA500IDXUSD", "USA30IDXUSD"),
    ("US500/US2000", "USA500IDXUSD", "USSC2000IDXUSD"),
    ("GER40/EU50", "DEUIDXEUR", "EUSIDXEUR"),
    ("FRA40/EU50", "FRAIDXEUR", "EUSIDXEUR"),
    ("GER40/FRA40", "DEUIDXEUR", "FRAIDXEUR"),
    ("UK100/EU50", "GBRIDXGBP", "EUSIDXEUR"),
    ("Oro/plata", "XAUUSD", "XAGUSD"),
    ("EURUSD/GBPUSD", "EURUSD", "GBPUSD"),
    ("AUDUSD/NZDUSD", "AUDUSD", "NZDUSD"),
    ("Brent/WTI", "BRENTCMDUSD", "LIGHTCMDUSD"),
]

# Spread por pata y lado, en fracción del nocional.
SPREAD = {"IDX": 0.0002, "FX": 0.0001, "METAL": 0.0003, "OIL": 0.0005}
FINANCIACION = 0.03  # anual sobre el nocional de cada pata


def clase(sym: str) -> str:
    if "IDX" in sym:
        return "IDX"
    if sym.startswith(("XAU", "XAG")):
        return "METAL"
    if "CMD" in sym:
        return "OIL"
    return "FX"


@dataclass
class Params:
    beta_win: int = 120
    z_win: int = 60
    vol_win: int = 60
    entrada: float = 2.0
    salida: float = 0.5
    stop: float = 4.0
    max_dias: int = 20
    vol_obj: float = 0.01
    cost_mult: float = 1.0
    beta_diario: bool = False


@dataclass
class Trade:
    par: str
    entrada: str
    salida: str
    lado: int
    dias: int
    pnl: float  # % del capital, neto
    motivo: str


def load(sym: str, datos: Path = DATOS) -> dict[str, tuple[float, float]]:
    out = {}
    with open(datos / f"{sym}.csv", newline="") as f:
        for row in csv.DictReader(f):
            o, c = float(row["open"]), float(row["close"])
            # Dukascopy rellena algunos días sin negociación con o=h=l=c; se descartan los fines de semana.
            d = row["date"][:10]
            if date.fromisoformat(d).weekday() < 5 and o > 0 and c > 0:
                out[d] = (o, c)
    return out


def align(a: dict, b: dict, hasta: str = FIN) -> tuple[list[str], list[float], list[float], list[float], list[float]]:
    dates = sorted(d for d in a.keys() & b.keys() if d <= hasta)
    return (dates, [a[d][0] for d in dates], [a[d][1] for d in dates],
            [b[d][0] for d in dates], [b[d][1] for d in dates])


def ols_beta(x: list[float], y: list[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    sxy = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    return sxy / sxx if sxx > 0 else 0.0


def mean_sd(v: list[float]) -> tuple[float, float]:
    n = len(v)
    m = sum(v) / n
    var = sum((x - m) ** 2 for x in v) / (n - 1)
    return m, math.sqrt(var)


def zscores(ca: list[float], cb: list[float], p: Params, beta_diario: bool = False) -> list[float | None]:
    """z del diferencial al cierre de t, usando solo datos hasta t.

    Por defecto aplica el β de hoy a los `z_win` días anteriores. Con `beta_diario` cada
    diferencial histórico usa su propio β, la versión original del preregistro, que mide sobre
    todo el ruido del β (ver informes/pares-preregistro.md).
    """
    la, lb = [math.log(x) for x in ca], [math.log(x) for x in cb]
    z: list[float | None] = [None] * len(la)
    betas: list[float | None] = [None] * len(la)
    for t in range(p.beta_win - 1, len(la)):
        lo = t - p.beta_win + 1
        betas[t] = ols_beta(lb[lo:t + 1], la[lo:t + 1])
    for t in range(max(p.beta_win - 1, p.z_win), len(la)):
        b = betas[t]
        if beta_diario:
            if any(x is None for x in betas[t - p.z_win:t]):
                continue
            hist = [la[k] - betas[k] * lb[k] for k in range(t - p.z_win, t)]  # type: ignore[operator]
        else:
            hist = [la[k] - b * lb[k] for k in range(t - p.z_win, t)]  # type: ignore[operator]
        m, sd = mean_sd(hist)
        if sd > 0:
            z[t] = (la[t] - b * lb[t] - m) / sd  # type: ignore[operator]
    return z


def sizes(ca: list[float], cb: list[float], t: int, p: Params) -> tuple[float, float]:
    """Nocional de cada pata (fracción del capital) para un par largo A / corto B."""
    ra = [math.log(ca[i] / ca[i - 1]) for i in range(t - p.vol_win + 1, t + 1)]
    rb = [math.log(cb[i] / cb[i - 1]) for i in range(t - p.vol_win + 1, t + 1)]
    _, va = mean_sd(ra)
    _, vb = mean_sd(rb)
    combo = [ra[i] / va - rb[i] / vb for i in range(len(ra))]
    _, vc = mean_sd(combo)
    k = p.vol_obj / vc
    return k / va, k / vb


def backtest(name: str, sa: str, sb: str, p: Params, datos: Path = DATOS) -> tuple[list[Trade], dict[str, float]]:
    dates, oa, ca, ob, cb = align(load(sa, datos), load(sb, datos))
    z = zscores(ca, cb, p, p.beta_diario)
    spa, spb = SPREAD[clase(sa)] * p.cost_mult, SPREAD[clase(sb)] * p.cost_mult
    fin = FINANCIACION * p.cost_mult / 365
    trades: list[Trade] = []
    daily: dict[str, float] = {}
    start = max(p.beta_win + p.z_win, p.vol_win + 1)
    t = start
    while t < len(dates) - 1:
        zt = z[t]
        if zt is None or abs(zt) <= p.entrada or abs(zt) >= p.stop:
            t += 1
            continue
        lado = -1 if zt > 0 else 1  # +1 = largo A / corto B
        na, nb = sizes(ca, cb, t, p)
        na, nb = lado * na, -lado * nb
        e = t + 1
        pnl = -(abs(na) * spa + abs(nb) * spb)
        day = pnl + na * (ca[e] / oa[e] - 1) + nb * (cb[e] / ob[e] - 1)
        daily[dates[e]] = daily.get(dates[e], 0.0) + day
        pnl = day
        i, motivo = e, "tiempo"
        while True:
            zi = z[i]
            held = i - e + 1
            if zi is not None and abs(zi) < p.salida:
                motivo = "media"
            elif zi is not None and abs(zi) > p.stop:
                motivo = "stop"
            elif held >= p.max_dias:
                motivo = "tiempo"
            elif i + 1 >= len(dates) - 1:
                motivo = "fin"
            else:
                motivo = ""
            nights = (date.fromisoformat(dates[i + 1]) - date.fromisoformat(dates[i])).days
            carry = -(abs(na) + abs(nb)) * fin * nights
            if motivo:
                # sale en la apertura siguiente
                day = carry + na * (oa[i + 1] / ca[i] - 1) + nb * (ob[i + 1] / cb[i] - 1)
                day -= abs(na) * spa + abs(nb) * spb
                daily[dates[i + 1]] = daily.get(dates[i + 1], 0.0) + day
                pnl += day
                trades.append(Trade(name, dates[e], dates[i + 1], lado, held, pnl * 100, motivo))
                t = i + 1
                break
            day = carry + na * (ca[i + 1] / ca[i] - 1) + nb * (cb[i + 1] / cb[i] - 1)
            daily[dates[i + 1]] = daily.get(dates[i + 1], 0.0) + day
            pnl += day
            i += 1
    return trades, {d: v * 100 for d, v in daily.items()}


def stats(pnls: list[float]) -> dict[str, float]:
    n = len(pnls)
    if n < 2:
        return {"n": n, "media": pnls[0] if n else 0.0, "t": 0.0, "acierto": 0.0, "total": sum(pnls)}
    m, sd = mean_sd(pnls)
    return {"n": n, "media": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else 0.0,
            "acierto": sum(x > 0 for x in pnls) / n * 100, "total": sum(pnls)}


def run_all(p: Params, datos: Path = DATOS) -> dict[str, list[Trade]]:
    return {name: backtest(name, a, b, p, datos)[0] for name, a, b in PARES}


def split(trades: list[Trade]) -> tuple[list[float], list[float]]:
    return [x.pnl for x in trades if x.entrada < CORTE], [x.pnl for x in trades if x.entrada >= CORTE]


def veredicto(res: dict[str, list[Trade]]) -> dict[str, object]:
    ins = [x for tr in res.values() for x in split(tr)[0]]
    oos = [x for tr in res.values() for x in split(tr)[1]]
    pos = sum(1 for tr in res.values() if sum(split(tr)[1]) > 0)
    s_in, s_oos = stats(ins), stats(oos)
    ok = s_oos["media"] > 0 and s_oos["t"] > 2 and pos >= 7 and s_in["media"] > 0
    return {"in": s_in, "oos": s_oos, "pares_pos": pos, "aprobado": ok}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datos", type=Path, default=DATOS)
    ap.add_argument("--cost-mult", type=float, default=1.0)
    ap.add_argument("--sensibilidad", action="store_true")
    ap.add_argument("--beta-diario", action="store_true", help="versión original del preregistro")
    a = ap.parse_args(argv)

    p = Params(cost_mult=a.cost_mult, beta_diario=a.beta_diario)
    res = run_all(p, a.datos)
    print(f"Pares, costes x{a.cost_mult:g}. % del capital por operación, vol objetivo 1 %/día.")
    print(f"{'Par':<15} {'n IS':>5} {'media IS':>9} {'t IS':>6} {'n OOS':>6} {'media OOS':>10} {'t OOS':>6} {'acierto':>8}")
    for name, tr in res.items():
        si, so = stats(split(tr)[0]), stats(split(tr)[1])
        print(f"{name:<15} {si['n']:>5} {si['media']:>+9.3f} {si['t']:>6.2f} {so['n']:>6} {so['media']:>+10.3f} {so['t']:>6.2f} {so['acierto']:>7.0f}%")
    v = veredicto(res)
    si, so = v["in"], v["oos"]
    print(f"{'TODOS':<15} {si['n']:>5} {si['media']:>+9.3f} {si['t']:>6.2f} {so['n']:>6} {so['media']:>+10.3f} {so['t']:>6.2f} {so['acierto']:>7.0f}%")
    print(f"Pares positivos fuera de muestra: {v['pares_pos']}/11. Veredicto: {'APROBADO' if v['aprobado'] else 'NO PASA'}")

    if a.sensibilidad:
        print("\nSensibilidad (solo informativa): media OOS / t OOS / pares positivos")
        for entrada in (1.5, 2.0, 2.5):
            for z_win in (20, 60, 120):
                q = Params(entrada=entrada, z_win=z_win, cost_mult=a.cost_mult, beta_diario=a.beta_diario)
                w = veredicto(run_all(q, a.datos))
                print(f"  entrada {entrada:<4} z {z_win:<4} IS {w['in']['media']:+.3f} (t {w['in']['t']:.2f})  "
                      f"OOS {w['oos']['media']:+.3f} (t {w['oos']['t']:.2f}, n {w['oos']['n']})  {w['pares_pos']}/11")


if __name__ == "__main__":
    main()
