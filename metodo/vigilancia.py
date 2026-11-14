"""Vigilancia en real de un EA (sustituye la regla "parar si R media < 0 tras 100 ops").

Fallo 1 de la auditoría v4 (`metodo/v4/AUDITORIA.md`): con la dispersión del ORB v018 (σ 1,80 R) esa regla
mata un ORB bueno el 25 % de las veces y deja vivo uno muerto el 49 %. Se sustituye por dos controles:

(a) **Cruce de ejecución diario** (detecta fallos en semanas): cada día real se compara con la réplica del
    mismo día (Strategy Tester con ticks reales o réplica Python). Debe coincidir que haya operación, el lado y
    la R (dentro de una tolerancia por deslizamiento).
(b) **SPRT de Wald acumulado** (freno de fondo, tarda años): H1 edge = +0,12 R frente a H0 edge = 0,
    α 5 %, β 20 %. Con edge real para por error ~18 % y confirma ~76 %; sin edge para ~92 %.

Con varianza conocida, el SPRT equivale a vigilar la **suma de R netas** S tras n operaciones:
    parar      si S <= lo·σ²/μ1 + n·μ1/2      (con los valores por defecto: S <= −42,1 + 0,06·n)
    confirmar  si S >= hi·σ²/μ1 + n·μ1/2      (S >= +74,9 + 0,06·n)
Así se puede seguir a mano en una hoja de cálculo.

Uso:
    python -m metodo.vigilancia real.csv replica.csv
    python -m metodo.vigilancia ORB_US100_ops.csv replica.csv --mt5 --riesgo-eur 2000

`real.csv` y `replica.csv`: columnas fecha, lado (largo/corto) y R (neta). Con `--mt5` el archivo real es el
CSV de `PlantillaPropEA.mq5` (Common/Files/<EA>_<símbolo>_ops.csv) y la R se calcula como
(beneficio + comisión + swap) / riesgo en euros por operación.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Parámetros del ORB v018 (auditoría v4): edge del backtest y dispersión de sus R.
MU1, SIGMA, ALFA, BETA = 0.12, 1.80, 0.05, 0.20


# ---------------------------------------------------------------- (b) SPRT
def limites_sprt(mu1=MU1, sigma=SIGMA, alfa=ALFA, beta=BETA):
    """Devuelve (corte inferior, corte superior, pendiente) en suma de R: S_lim(n) = corte + pendiente·n."""
    lo, hi = np.log(beta / (1 - alfa)), np.log((1 - beta) / alfa)
    k = sigma ** 2 / mu1
    return lo * k, hi * k, mu1 / 2


@dataclass
class EstadoSPRT:
    n: int
    suma_r: float
    limite_parar: float
    limite_confirmar: float
    estado: str  # "seguir", "parar" o "confirmado"
    decidido_en: int | None  # operación en la que se cruzó un límite (el primero que se cruza manda)

    def __str__(self):
        txt = (f"SPRT: {self.n} ops, suma R {self.suma_r:+.1f} (parar si <= {self.limite_parar:+.1f}, "
               f"confirmar si >= {self.limite_confirmar:+.1f}) -> {self.estado.upper()}")
        if self.decidido_en is not None:
            txt += f" en la operación {self.decidido_en}"
        return txt


def sprt(r, mu1=MU1, sigma=SIGMA, alfa=ALFA, beta=BETA) -> EstadoSPRT:
    """SPRT gaussiano sobre la secuencia de R netas en orden cronológico. La decisión es definitiva:
    se queda con el primer límite cruzado aunque la suma vuelva luego dentro de la banda."""
    r = np.asarray(r, float)
    c_lo, c_hi, p = limites_sprt(mu1, sigma, alfa, beta)
    n = np.arange(1, len(r) + 1)
    s = np.cumsum(r)
    abajo, arriba = s <= c_lo + p * n, s >= c_hi + p * n
    estado, en = "seguir", None
    if abajo.any() or arriba.any():
        i_ab = abajo.argmax() if abajo.any() else len(r)
        i_ar = arriba.argmax() if arriba.any() else len(r)
        estado, en = ("parar", i_ab + 1) if i_ab < i_ar else ("confirmado", i_ar + 1)
    total = len(r)
    return EstadoSPRT(total, float(s[-1]) if total else 0.0, c_lo + p * total, c_hi + p * total, estado, en)


# ---------------------------------------------------------------- (a) cruce de ejecución
def cruce(real: pd.DataFrame, replica: pd.DataFrame, tol_r=0.25) -> pd.DataFrame:
    """Une por fecha y marca cada día: ok, falta_real, falta_replica, lado o r (|ΔR| > tol_r).
    Si un día tiene varias operaciones se suman sus R y se toma el lado de la primera."""
    def por_dia(df):
        d = df.assign(fecha=pd.to_datetime(df["fecha"]).dt.normalize())
        return d.groupby("fecha").agg(lado=("lado", "first"), R=("R", "sum"))

    m = por_dia(real).join(por_dia(replica), how="outer", lsuffix="_real", rsuffix="_replica")
    m["dif_R"] = m["R_real"] - m["R_replica"]
    m["estado"] = "ok"
    m.loc[m["R_real"].isna(), "estado"] = "falta_real"
    m.loc[m["R_replica"].isna(), "estado"] = "falta_replica"
    ambos = m["R_real"].notna() & m["R_replica"].notna()
    m.loc[ambos & (m["dif_R"].abs() > tol_r), "estado"] = "r"
    m.loc[ambos & (m["lado_real"] != m["lado_replica"]), "estado"] = "lado"
    return m.reset_index()


def alerta_ejecucion(m: pd.DataFrame, ultimos=20, max_fallos=0.10):
    """Alerta si en los últimos `ultimos` días con operación más del `max_fallos` no coincide."""
    reciente = m.tail(ultimos)
    tasa = float((reciente["estado"] != "ok").mean()) if len(reciente) else 0.0
    return tasa > max_fallos, tasa


# ---------------------------------------------------------------- lectura
def leer_mt5(ruta, riesgo_eur: float) -> pd.DataFrame:
    """CSV de PlantillaPropEA.mq5 (sep ';'): una fila por cierre. tipo 'cierra_largo' = la posición era larga."""
    d = pd.read_csv(ruta, sep=";")
    neto = d["beneficio"] + d["comision"] + d["swap"]
    # Un cierre parcial genera varias filas de la misma posición: se suman.
    g = d.assign(neto=neto).groupby("posicion").agg(fecha=("cierre", "first"), tipo=("tipo", "first"),
                                                    neto=("neto", "sum"))
    lado = np.where(g["tipo"] == "cierra_largo", "largo", "corto")
    return pd.DataFrame({"fecha": pd.to_datetime(g["fecha"]), "lado": lado,
                         "R": g["neto"] / riesgo_eur}).sort_values("fecha").reset_index(drop=True)


def leer(ruta) -> pd.DataFrame:
    d = pd.read_csv(ruta, sep=None, engine="python")
    d["fecha"] = pd.to_datetime(d["fecha"])
    return d.sort_values("fecha").reset_index(drop=True)


def informe(real: pd.DataFrame, replica: pd.DataFrame, tol_r=0.25) -> str:
    m = cruce(real, replica, tol_r)
    alerta, tasa = alerta_ejecucion(m)
    malos = m[m["estado"] != "ok"]
    lineas = [f"Cruce real vs réplica: {len(m)} días, {len(malos)} no coinciden "
              f"({(m['estado'].value_counts().to_dict())})",
              f"Últimos 20 días: {tasa:.0%} de fallos -> {'ALERTA: revisar ejecución' if alerta else 'ok'}"]
    if len(malos):
        lineas.append("Días que no coinciden (últimos 10):")
        lineas.append(malos.tail(10).to_string(index=False, float_format=lambda x: f"{x:+.2f}"))
    lineas.append(str(sprt(real["R"])))
    lineas.append(f"R media real {real['R'].mean():+.3f} en {len(real)} ops (no decide nada por sí sola).")
    return "\n".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("real")
    ap.add_argument("replica")
    ap.add_argument("--mt5", action="store_true", help="el archivo real es el CSV de PlantillaPropEA.mq5")
    ap.add_argument("--riesgo-eur", type=float, help="riesgo por operación en euros (necesario con --mt5)")
    ap.add_argument("--tol-r", type=float, default=0.25)
    a = ap.parse_args(argv)
    if a.mt5 and not a.riesgo_eur:
        ap.error("--mt5 necesita --riesgo-eur")
    real = leer_mt5(a.real, a.riesgo_eur) if a.mt5 else leer(a.real)
    print(informe(real, leer(a.replica), a.tol_r))


if __name__ == "__main__":
    main()
