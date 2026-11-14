"""P5: compara operación a operación el backtest de Python con el Strategy Tester de MT5.

Comparar solo nº de ops y R media (±20 %) esconde errores que se compensan. Aquí se empareja
cada operación por lado y hora (con tolerancia) y se listan las que solo están en un lado y las
de mayor diferencia en R: ahí suele estar el fallo (hora del servidor, hueco de apertura, stop
tocado dentro de la vela, filtro que en MQL5 se evalúa en otra vela...).

Formatos de MT5 que se leen solos (`cargar_mt5`):
  - PlantillaPropEA.mq5: cierre;posicion;tipo;volumen;precio;beneficio;comision;swap
    [+ apertura;precio_entrada;sl_inicial;r_bruto desde el 14-11-2026]
  - ORB_US100_AGR (ORB_*.csv): Fecha;Hora;Simbolo;Lado;...;PrecioEntrada;...;R;...
    (ahí Fecha/Hora es la SALIDA: compara con la hora de salida de Python)

Python: DataFrame con columnas hora (datetime de entrada, o de salida si se compara por
salida), lado (+1 largo / −1 corto) y r; precio_entrada es opcional.

    from metodo.comparar_ops import cargar_mt5, comparar
    print(comparar(ops_python, cargar_mt5("ORB_AGR_v018_live.csv"), tolerancia="5min"))

Uso desde la terminal:  python -m metodo.comparar_ops python.csv mt5.csv [--tolerancia 5min]
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_EMPAREJADAS = 0.90    # fracción mínima de ops de cada lado que deben emparejarse
MAX_DIF_MEDIA = 0.20      # |R media MT5 − R media Python| / |R media Python| ...
MAX_DIF_ABS = 0.02        # ... o, si la media es casi 0, diferencia absoluta en R
MIN_CERCANAS = 0.90       # fracción de pares con |ΔR| ≤ MAX_DR
MIN_CORR = 0.90           # correlación de R entre pares: detecta errores que se compensan
MAX_DR = 0.10             # diferencia de R aceptable por operación (deslizamiento, spread)


def _lado(x) -> int:
    if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x):
        return 1 if x > 0 else -1
    s = str(x).strip().lower()
    if s.startswith(("b", "l", "compra", "larg", "cierra_largo", "+")):
        return 1
    if s.startswith(("s", "v", "corto", "cierra_corto", "-")):
        return -1
    raise ValueError(f"lado desconocido: {x!r}")


def cargar_mt5(ruta: str, sep: str = ";") -> pd.DataFrame:
    """Lee el CSV de operaciones de un EA y devuelve hora, lado, r, precio_entrada."""
    with open(ruta, "rb") as f:
        crudo = f.read(4)
    cod = "utf-16" if crudo[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    df = pd.read_csv(ruta, sep=sep, encoding=cod)
    cols = {c.lower(): c for c in df.columns}
    if "fecha" in cols and "hora" in cols and "r" in cols:          # ORB_US100_AGR
        out = pd.DataFrame({
            "hora": pd.to_datetime(df[cols["fecha"]].astype(str) + " " + df[cols["hora"]].astype(str)),
            "lado": df[cols["lado"]].map(_lado),
            "r": pd.to_numeric(df[cols["r"]], errors="coerce"),
        })
        if "precioentrada" in cols:
            out["precio_entrada"] = pd.to_numeric(df[cols["precioentrada"]], errors="coerce")
        return out
    if "cierre" in cols and "tipo" in cols:                          # PlantillaPropEA
        if "r_bruto" not in cols:
            raise ValueError("CSV de la plantilla antiguo (sin apertura/r_bruto): borra el CSV y "
                             "repite el backtest con la plantilla del 14-11-2026 o posterior")
        return pd.DataFrame({
            "hora": pd.to_datetime(df[cols["apertura"]], format="%Y.%m.%d %H:%M:%S"),
            "lado": df[cols["tipo"]].map(_lado),
            "r": pd.to_numeric(df[cols["r_bruto"]], errors="coerce"),
            "precio_entrada": pd.to_numeric(df[cols["precio_entrada"]], errors="coerce"),
        })
    raise ValueError(f"formato de CSV no reconocido: columnas {list(df.columns)}")


@dataclass
class Comparacion:
    pares: pd.DataFrame
    solo_python: pd.DataFrame
    solo_mt5: pd.DataFrame
    n_python: int
    n_mt5: int

    @property
    def resumen(self) -> dict:
        p = self.pares
        media_py, media_mt = (p.r_py.mean(), p.r_mt5.mean()) if len(p) else (np.nan, np.nan)
        dif_abs = abs(media_mt - media_py) if len(p) else np.inf
        dif = dif_abs / abs(media_py) if len(p) and media_py else np.inf
        return {
            "emparejadas_py": len(p) / self.n_python if self.n_python else 0.0,
            "emparejadas_mt5": len(p) / self.n_mt5 if self.n_mt5 else 0.0,
            "media_py": media_py, "media_mt5": media_mt, "dif_media": dif, "dif_abs": dif_abs,
            "corr_r": p.r_py.corr(p.r_mt5) if len(p) > 2 else np.nan,
            "cercanas": float((p.dr.abs() <= MAX_DR).mean()) if len(p) else 0.0,
        }

    @property
    def pasa(self) -> bool:
        r = self.resumen
        return (min(r["emparejadas_py"], r["emparejadas_mt5"]) >= MIN_EMPAREJADAS
                and (r["dif_media"] <= MAX_DIF_MEDIA or r["dif_abs"] <= MAX_DIF_ABS)
                and r["cercanas"] >= MIN_CERCANAS and r["corr_r"] >= MIN_CORR)

    def __str__(self) -> str:
        r = self.resumen
        lin = [
            f"Python {self.n_python} ops, MT5 {self.n_mt5} ops, emparejadas {len(self.pares)} "
            f"({r['emparejadas_py']:.0%} de Python, {r['emparejadas_mt5']:.0%} de MT5; mín {MIN_EMPAREJADAS:.0%})",
            f"R media en pares: Python {r['media_py']:+.3f}, MT5 {r['media_mt5']:+.3f} "
            f"(diferencia {r['dif_media']:.0%} = {r['dif_abs']:.3f} R; máx {MAX_DIF_MEDIA:.0%} o {MAX_DIF_ABS} R); "
            f"corr {r['corr_r']:.3f} (mín {MIN_CORR})",
            f"Pares con |ΔR| ≤ {MAX_DR}: {r['cercanas']:.0%} (mín {MIN_CERCANAS:.0%})",
        ]
        if len(self.pares):
            peor = self.pares.reindex(self.pares.dr.abs().sort_values(ascending=False).index).head(10)
            lin.append("Mayores diferencias (empieza a buscar aquí):")
            lin += ["  " + f"{f.hora_py:%Y-%m-%d %H:%M} lado {f.lado:+d} R py {f.r_py:+.2f} mt5 {f.r_mt5:+.2f} "
                    f"Δt {f.dt_min:+.0f} min" + (f" Δentrada {f.dprecio:+.2f}" if "dprecio" in f._fields and pd.notna(f.dprecio) else "")
                    for f in peor.itertuples()]
        for nombre, d in (("Solo en Python", self.solo_python), ("Solo en MT5", self.solo_mt5)):
            if len(d):
                lin.append(f"{nombre} ({len(d)}), primeras 10:")
                lin += [f"  {f.hora:%Y-%m-%d %H:%M} lado {f.lado:+d} R {f.r:+.2f}" for f in d.head(10).itertuples()]
        lin.append("VEREDICTO P5: " + ("coinciden" if self.pasa else "NO coinciden: buscar el fallo antes de seguir"))
        return "\n".join(lin)


def comparar(py: pd.DataFrame, mt5: pd.DataFrame, tolerancia: str = "5min",
             desfase: str = "0min") -> Comparacion:
    """Empareja por lado y hora más cercana dentro de `tolerancia`.

    desfase: se suma a las horas de Python antes de emparejar (p. ej. "7h" si Python va en hora
    de NY y MT5 en hora del servidor NY+7). Si casi nada empareja, probar primero el desfase.
    """
    a = py[["hora", "lado", "r"] + (["precio_entrada"] if "precio_entrada" in py else [])].copy()
    a["hora"] = pd.to_datetime(a.hora) + pd.Timedelta(desfase)
    a["lado"] = a.lado.map(_lado)
    b = mt5.copy()
    b["hora"] = pd.to_datetime(b.hora)
    a = a.sort_values("hora").reset_index(drop=True)
    b = b.sort_values("hora").reset_index(drop=True)
    tol = pd.Timedelta(tolerancia)

    usadas: set[int] = set()
    filas, sin_par = [], []
    horas_b = b.hora.to_numpy()
    for i, f in a.iterrows():
        lo = np.searchsorted(horas_b, np.datetime64(f.hora - tol), "left")
        hi = np.searchsorted(horas_b, np.datetime64(f.hora + tol), "right")
        cand = [j for j in range(lo, hi) if j not in usadas and b.lado[j] == f.lado]
        if not cand:
            sin_par.append(i)
            continue
        j = min(cand, key=lambda k: abs(b.hora[k] - f.hora))
        usadas.add(j)
        fila = {"hora_py": f.hora, "hora_mt5": b.hora[j], "lado": int(f.lado), "r_py": f.r,
                "r_mt5": b.r[j], "dt_min": (b.hora[j] - f.hora).total_seconds() / 60}
        if "precio_entrada" in a and "precio_entrada" in b:
            fila["dprecio"] = b.precio_entrada[j] - f.precio_entrada
        filas.append(fila)
    pares = pd.DataFrame(filas, columns=["hora_py", "hora_mt5", "lado", "r_py", "r_mt5", "dt_min"]
                         + (["dprecio"] if filas and "dprecio" in filas[0] else []))
    pares["dr"] = pares.r_mt5 - pares.r_py
    solo_mt5 = b.loc[[j for j in range(len(b)) if j not in usadas]]
    return Comparacion(pares, a.loc[sin_par], solo_mt5, len(a), len(b))


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("python_csv", help="CSV con hora, lado, r (y opcional precio_entrada)")
    ap.add_argument("mt5_csv", help="CSV de operaciones del EA (plantilla u ORB)")
    ap.add_argument("--tolerancia", default="5min")
    ap.add_argument("--desfase", default="0min")
    a = ap.parse_args()
    py = pd.read_csv(a.python_csv, parse_dates=["hora"])
    print(comparar(py, cargar_mt5(a.mt5_csv), a.tolerancia, a.desfase))


if __name__ == "__main__":
    _main()
