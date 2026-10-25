"""Backtest preregistrado de la continuación del gap de resultados (informes/gap-resultados-preregistro.md).

Uso: python -m lab.gap_resultados            # informe completo
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from lab.acciones import AMPLIO, FTMO, OUT_DIR

CORTE = "2018-01-01"


@dataclass(frozen=True)
class Regla:
    gap: float = 0.03
    vol_x: float = 3.0
    ret: float = 0.03
    atr_k: float = 2.0
    sesiones: int = 5
    stop: bool = True


def cargar(sym: str) -> pd.DataFrame | None:
    path = OUT_DIR / f"{sym}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["d"]).drop_duplicates("d").set_index("d").sort_index()
    return df[(df.v > 0) & (df.c > 0)]


def operaciones(sym: str, df: pd.DataFrame, r: Regla, coste: float, swap: float) -> list[dict]:
    o, h, l, c, v = (df[k].to_numpy(float) for k in "ohlcv")
    fechas = df.index
    pc = np.roll(c, 1)
    tr = np.maximum(h, pc) - np.minimum(l, pc)
    tr[0] = h[0] - l[0]
    atr = pd.Series(tr).rolling(20).mean().shift(1).to_numpy()
    vmed = pd.Series(v).rolling(20).mean().shift(1).to_numpy()
    ops, libre = [], 0
    for i in range(21, len(c) - 1):
        if i < libre or not (atr[i] > 0 and vmed[i] > 0):
            continue
        gap, ret = o[i] / c[i - 1] - 1, c[i] / c[i - 1] - 1
        if abs(gap) < r.gap or v[i] < r.vol_x * vmed[i] or abs(ret) < r.ret or gap * ret <= 0:
            continue
        d = 1.0 if ret > 0 else -1.0
        entrada, riesgo = c[i], r.atr_k * atr[i]
        stop = entrada - d * riesgo
        fin = min(i + r.sesiones, len(c) - 1)
        salida, j = c[fin], fin
        if r.stop:
            for k in range(i + 1, fin + 1):
                if d * (o[k] - stop) <= 0:
                    salida, j = o[k], k
                    break
                if d * ((l[k] if d > 0 else h[k]) - stop) <= 0:
                    salida, j = stop, k
                    break
        noches = (fechas[j] - fechas[i]).days
        bruto = d * (salida - entrada) / riesgo
        neto = bruto - entrada * (coste + swap * noches) / riesgo
        # P&L diario a precio de cierre, para correlaciones
        diario = {}
        prev = entrada
        for k in range(i + 1, j + 1):
            px = salida if k == j else c[k]
            diario[fechas[k]] = d * (px - prev) / riesgo
            prev = px
        if diario:
            diario[fechas[j]] -= entrada * (coste + swap * noches) / riesgo
        ops.append(dict(sym=sym, fecha=fechas[i], dir=d, bruto=bruto, neto=neto,
                        mov=d * (salida - entrada) / entrada, diario=diario))
        libre = j + 1
    return ops


def correr(syms: list[str], r: Regla, mult: float = 1.0) -> pd.DataFrame:
    todas = []
    for s in syms:
        df = cargar(s)
        if df is not None:
            todas += operaciones(s, df, r, 0.001 * mult, 0.0002 * mult)
    return pd.DataFrame(todas)


def resumen(ops: pd.DataFrame, col: str = "neto") -> str:
    if ops.empty:
        return "sin operaciones"
    x = ops[col]
    t = x.mean() / x.std(ddof=1) * math.sqrt(len(x)) if len(x) > 1 else float("nan")
    gan = x[x > 0].sum()
    pf = gan / -x[x < 0].sum() if (x < 0).any() else float("inf")
    return (f"n={len(x):5d}  R/op={x.mean():+.3f}  t={t:+.2f}  PF={pf:.2f}  "
            f"acierto={(x > 0).mean():.0%}  mov medio={ops.mov.mean():+.2%}")


def serie_diaria(ops: pd.DataFrame) -> pd.Series:
    s: dict = {}
    for dct in ops.diario:
        for k, val in dct.items():
            s[k] = s.get(k, 0.0) + val
    return pd.Series(s).sort_index()


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    base = Regla()
    amplio = FTMO + AMPLIO
    print("Regla preregistrada:", base)
    for nombre, syms in (("AMPLIO", amplio), ("FTMO", FTMO)):
        for mult in (1.0, 2.0):
            ops = correr(syms, base, mult)
            dentro, fuera = ops[ops.fecha < CORTE], ops[ops.fecha >= CORTE]
            print(f"\n== {nombre}, costes x{mult:g} ==")
            print("  bruto fuera   ", resumen(fuera, "bruto"))
            print("  2005-2017     ", resumen(dentro))
            print("  2018-2026     ", resumen(fuera))
            print("    largos      ", resumen(fuera[fuera.dir > 0]))
            print("    cortos      ", resumen(fuera[fuera.dir < 0]))
            if mult == 1.0:
                por_anio = fuera.groupby(fuera.fecha.dt.year).neto.agg(["count", "mean", "sum"])
                print("  por año (fuera):")
                print(por_anio.round(3).to_string())
                print(f"  años positivos: {(por_anio['sum'] > 0).sum()} de {len(por_anio)}")
                qqq = cargar("QQQ")
                if qqq is not None:
                    pnl = serie_diaria(fuera)
                    rq = qqq.c.pct_change().reindex(pnl.index)
                    print(f"  correlación P&L diario con QQQ: {pnl.corr(rq):+.3f}  "
                          f"(días con posición: {len(pnl)})")
    print("\n== Sensibilidad, AMPLIO 2018-2026, costes x1 (solo contexto) ==")
    variantes = {
        "1 sesión": Regla(sesiones=1), "3 sesiones": Regla(sesiones=3),
        "10 sesiones": Regla(sesiones=10), "gap 2 %": Regla(gap=0.02),
        "gap 5 %": Regla(gap=0.05), "volumen x2": Regla(vol_x=2.0),
        "volumen x5": Regla(vol_x=5.0), "sin stop": Regla(stop=False),
    }
    for nombre, reg in variantes.items():
        ops = correr(amplio, reg)
        print(f"  {nombre:12s}", resumen(ops[ops.fecha >= CORTE]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
