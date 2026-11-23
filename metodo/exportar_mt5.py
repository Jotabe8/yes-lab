"""Exporta las operaciones cerradas de una cuenta MT5 a `fecha, lado, R` y pasa la vigilancia (SPRT).

Se ejecuta en el PC de Windows con el terminal MT5 abierto y conectado (paquete oficial `MetaTrader5`):

    pip install MetaTrader5 pandas numpy
    python -m metodo.exportar_mt5 --simbolo US100.cash --desde 2026-10-01 --salida ops_mt5.csv
    python -m metodo.exportar_mt5 --simbolo US100.cash --replica replica.csv     # además, cruce con la réplica

Con varios terminales abiertos, `--terminal "C:\\...\\terminal64.exe"` elige el de la cuenta real.

Cálculo de R (igual que el informe diario del EA: el 6-11 da −0,934): R = lado × (salida − entrada) / |entrada − stop
inicial|, con el stop inicial de la orden de entrada; si la orden no lleva stop (el EA lo pone después) se toma el de la
primera modificación registrada en la posición y, si tampoco hay, `--riesgo-pct` del balance previo. La R neta descuenta
comisión, swap y fee convertidos a R con el valor monetario por punto de la propia operación.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

ENTRADA, SALIDA = 0, 1  # DEAL_ENTRY_IN, DEAL_ENTRY_OUT (2 = INOUT, 3 = OUT_BY también cierran)
COMPRA, VENTA, BALANCE = 0, 1, 2


def _df(registros) -> pd.DataFrame:
    if registros is None or len(registros) == 0:
        return pd.DataFrame()
    return pd.DataFrame([r._asdict() if hasattr(r, "_asdict") else dict(r) for r in registros])


def operaciones(deals: pd.DataFrame, ordenes: pd.DataFrame, simbolo=None, magic=None, riesgo_pct=None) -> pd.DataFrame:
    """Convierte deals + órdenes del historial MT5 en una fila por posición cerrada (fecha, lado, R, r_bruta, ...)."""
    if deals.empty:
        return pd.DataFrame(columns=["fecha", "lado", "R", "r_bruta", "stop_origen", "posicion"])
    d = deals.sort_values(["time", "ticket"]).copy()
    d["neto"] = d["profit"] + d.get("commission", 0) + d.get("swap", 0) + d.get("fee", 0)
    d["balance_tras"] = d["neto"].cumsum()  # incluye depósitos (DEAL_TYPE_BALANCE)
    d["balance_antes"] = d["balance_tras"] - d["neto"]
    t = d[d["type"].isin([COMPRA, VENTA])]
    if simbolo:
        t = t[t["symbol"] == simbolo]
    if magic is not None:
        t = t[t["magic"] == magic]
    sl_orden = {}
    if not ordenes.empty and "sl" in ordenes:
        o = ordenes.sort_values("time_setup")
        for _, fila in o.iterrows():
            if fila["sl"] and fila.get("position_id", 0):
                sl_orden.setdefault(int(fila["position_id"]), (int(fila["ticket"]), float(fila["sl"])))
    filas = []
    for pos, g in t.groupby("position_id"):
        ent, sal = g[g["entry"] == ENTRADA], g[g["entry"] != ENTRADA]
        if ent.empty or sal.empty:
            continue  # posición abierta o historial incompleto
        e = ent.iloc[0]
        lado = 1 if e["type"] == COMPRA else -1
        p_ent = float((ent["price"] * ent["volume"]).sum() / ent["volume"].sum())
        p_sal = float((sal["price"] * sal["volume"]).sum() / sal["volume"].sum())
        bruto_dinero = float(g["profit"].sum())
        costes = float((g.get("commission", 0) + g.get("swap", 0) + g.get("fee", 0)).sum())
        mov = lado * (p_sal - p_ent)
        stop, origen = None, None
        orden_ent = int(e["order"]) if "order" in e else None
        if not ordenes.empty and orden_ent is not None and "sl" in ordenes:
            m = ordenes[ordenes["ticket"] == orden_ent]
            if len(m) and m.iloc[0]["sl"]:
                stop, origen = float(m.iloc[0]["sl"]), "orden"
        if stop is None and int(pos) in sl_orden:
            stop, origen = sl_orden[int(pos)][1], "posición"
        if stop is not None and abs(p_ent - stop) > 0:
            dist = abs(p_ent - stop)
            r_bruta = mov / dist
            dinero_por_punto = bruto_dinero / mov if mov else np.nan
            r = r_bruta + (costes / (dinero_por_punto * dist) if np.isfinite(dinero_por_punto) and dinero_por_punto else 0)
        elif riesgo_pct:
            riesgo = riesgo_pct / 100 * float(e["balance_antes"])
            r_bruta, r, origen = bruto_dinero / riesgo, (bruto_dinero + costes) / riesgo, f"{riesgo_pct} % balance"
        else:
            continue
        filas.append(dict(fecha=pd.to_datetime(sal.iloc[-1]["time"], unit="s"), lado="largo" if lado > 0 else "corto",
                          R=round(r, 4), r_bruta=round(r_bruta, 4), stop_origen=origen, posicion=int(pos),
                          simbolo=e["symbol"], neto=round(bruto_dinero + costes, 2)))
    return pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True) if filas else pd.DataFrame(
        columns=["fecha", "lado", "R", "r_bruta", "stop_origen", "posicion"])


def descargar(desde: datetime, hasta: datetime, terminal=None):
    import MetaTrader5 as mt5  # solo existe en Windows
    ok = mt5.initialize(path=terminal) if terminal else mt5.initialize()
    if not ok:
        raise SystemExit(f"No conecta con MT5: {mt5.last_error()}. ¿Está el terminal abierto y con sesión?")
    try:
        info = mt5.account_info()
        deals = _df(mt5.history_deals_get(desde, hasta))
        ordenes = _df(mt5.history_orders_get(desde, hasta))
    finally:
        mt5.shutdown()
    return info, deals, ordenes


def main(argv=None):
    ap = argparse.ArgumentParser(description="Operaciones MT5 → fecha, lado, R + SPRT")
    ap.add_argument("--simbolo", help="p. ej. US100.cash (por defecto, todos)")
    ap.add_argument("--magic", type=int, help="número mágico del EA (por defecto, todos)")
    ap.add_argument("--desde", default=None, help="AAAA-MM-DD (por defecto, 365 días atrás)")
    ap.add_argument("--terminal", help="ruta a terminal64.exe si hay varios MT5 abiertos")
    ap.add_argument("--riesgo-pct", type=float, help="respaldo si la operación no tiene stop en el historial")
    ap.add_argument("--salida", default="ops_mt5.csv")
    ap.add_argument("--replica", help="CSV fecha,lado,R de la réplica para el cruce diario")
    a = ap.parse_args(argv)
    desde = datetime.fromisoformat(a.desde) if a.desde else datetime.now() - timedelta(days=365)
    info, deals, ordenes = descargar(desde, datetime.now() + timedelta(days=1), a.terminal)
    ops = operaciones(deals, ordenes, a.simbolo, a.magic, a.riesgo_pct)
    ops.to_csv(a.salida, index=False)
    print(f"Cuenta {getattr(info, 'login', '?')} ({getattr(info, 'server', '?')}): {len(ops)} operaciones -> {a.salida}")
    if ops.empty:
        return
    print(ops[["fecha", "simbolo", "lado", "r_bruta", "R", "stop_origen"]].to_string(index=False))
    from metodo.vigilancia import informe, leer, sprt
    print()
    print(informe(ops, leer(a.replica)) if a.replica else sprt(ops["R"]))


if __name__ == "__main__":
    main()
