"""Libro de pruebas: apunta CADA evaluación de una familia de ideas, para que `n_pruebas` y la matriz
de variantes del DSR/PBO salgan del registro y no de la memoria de quien prueba.

Motivo (arXiv 2608.27734, "What survives honest evaluation?", 2026): contar las pruebas a mano las
infravalora siempre, y con eso el listón del t corregido y del Deflated Sharpe queda bajo.

Uso directo:

    from metodo.libro_pruebas import apuntar, contar, matriz
    apuntar("reversion_dz", {"ibs": 0.2, "maxd": 5, "mercados": "ES,NQ,RTY,YM"}, ops)
    contar("reversion_dz")          # nº de reglas distintas probadas en la familia
    matriz("reversion_dz")          # días × reglas con el R neto diario (para robustez.spa/pbo)

o a través del embudo: `embudo(ops, n_pruebas, corte, familia="reversion_dz", regla={...})`.

`ops` necesita fecha y r_neto (o r_bruto y coste_r). La misma regla (mismo diccionario) cuenta una
sola vez aunque se repita la evaluación. El libro vive en `metodo/libro/` (se sube al repo: es la
prueba de cuántas cosas se miraron). Otra carpeta: variable de entorno LIBRO_PRUEBAS_DIR.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNAS = ["registrado", "hash", "regla", "n_ops", "desde", "hasta", "r_media", "t_op"]


def _dir() -> Path:
    return Path(os.environ.get("LIBRO_PRUEBAS_DIR", Path(__file__).parent / "libro"))


def _limpio(familia: str) -> str:
    f = "".join(c if c.isalnum() or c in "-_" else "_" for c in familia.strip())
    if not f:
        raise ValueError("familia vacía")
    return f


def hash_regla(regla: dict) -> str:
    return hashlib.sha1(json.dumps(regla, sort_keys=True, default=str).encode()).hexdigest()[:12]


def apuntar(familia: str, regla: dict, ops: pd.DataFrame) -> str:
    """Apunta una evaluación. Devuelve el hash de la regla. Repetir la misma regla actualiza su fila."""
    fam = _limpio(familia)
    d = _dir()
    (d / fam).mkdir(parents=True, exist_ok=True)
    fechas = pd.to_datetime(ops["fecha"])
    r = (ops["r_neto"] if "r_neto" in ops else ops["r_bruto"] - ops["coste_r"]).to_numpy(float)
    h = hash_regla(regla)
    t = float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if len(r) > 1 and r.std(ddof=1) > 0 else 0.0
    fila = {"registrado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "hash": h,
            "regla": json.dumps(regla, sort_keys=True, default=str, ensure_ascii=False),
            "n_ops": len(r), "desde": fechas.min().date() if len(r) else "",
            "hasta": fechas.max().date() if len(r) else "",
            "r_media": round(float(r.mean()), 5) if len(r) else np.nan, "t_op": round(t, 3)}
    libro = leer(fam)
    libro = pd.concat([libro[libro.hash != h], pd.DataFrame([fila])], ignore_index=True)
    libro[COLUMNAS].to_csv(d / f"{fam}.csv", index=False)
    diaria = pd.Series(r, index=fechas.dt.normalize()).groupby(level=0).sum().rename("r")
    diaria.to_csv(d / fam / f"{h}.csv.gz", index_label="fecha")
    return h


def leer(familia: str) -> pd.DataFrame:
    p = _dir() / f"{_limpio(familia)}.csv"
    return pd.read_csv(p, dtype={"hash": str}) if p.exists() else pd.DataFrame(columns=COLUMNAS)


def contar(familia: str) -> int:
    """Número de reglas distintas evaluadas en la familia."""
    return int(leer(familia).hash.nunique())


def matriz(familia: str) -> pd.DataFrame:
    """Matriz días × reglas con el R neto diario (0 los días sin operar), lista para robustez.spa/pbo
    y para `embudo(..., variantes=...)`."""
    fam = _limpio(familia)
    cols = {}
    for h in leer(fam).hash:
        p = _dir() / fam / f"{h}.csv.gz"
        if p.exists():
            s = pd.read_csv(p, parse_dates=["fecha"]).set_index("fecha")["r"]
            cols[h] = s
    if not cols:
        return pd.DataFrame()
    m = pd.DataFrame(cols).sort_index()
    return m.fillna(0.0)
