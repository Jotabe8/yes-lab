"""P5 de la v019 (tope de pausa 21 días): réplica Python frente al Strategy Tester sin simulador y frente a la cuenta real.

Uso: python -m metodo.pruebas.orb_v019.validar_v019 <US100_cash_M1_FTMO.csv> <US100_..._2026-09-01_2026-10-29.csv>
Las operaciones se emparejan por día de entrada (máx. 1 al día): la hora de salida del CSV del EA se pasa al día de
entrada (si sale antes de las 16:40, la entrada fue el día hábil anterior).
"""
import sys
from pathlib import Path
import pandas as pd
from metodo.comparar_ops import cargar_mt5, comparar
from metodo.pruebas.orb_v019.replica import cargar, simular

AQUI = Path(__file__).parent / "datos"
ENTRADA = pd.Timedelta("16:40:00")


def por_dia(mt):
    d = mt.hora.dt.normalize()
    d = d.where(mt.hora.dt.hour * 60 + mt.hora.dt.minute >= 16 * 60 + 40, d - pd.offsets.BDay(1))
    return mt.assign(salida=mt.hora, hora=d + ENTRADA)


def detalle(c, py, mt):
    p = c.pares.assign(fecha=c.pares.hora_py.dt.normalize())
    p = p.merge(py[["fecha", "hora", "salida", "forzada"]].rename(columns={"hora": "sal_py", "salida": "tipo_py"}), on="fecha")
    p = p.merge(mt[["hora", "salida"]].rename(columns={"salida": "sal_mt5"}), left_on="hora_mt5", right_on="hora")
    return p


v = cargar(sys.argv[1], sys.argv[2], str(AQUI / "US100_cash_M1_FTMO_hasta_nov.csv"))
py = simular(v, tope_pausa=21, desde="2022-01-01")
pyd = py.assign(hora=py.fecha + ENTRADA)
print(f"Réplica: {len(py)} ops 2022-01 → {py.fecha.max():%Y-%m-%d}, R media {py.r.mean():+.3f}, forzadas {py.forzada.sum()}")
pd.set_option("display.width", 220)

mt = por_dia(cargar_mt5(str(AQUI / "v019tope_test_sinsim.csv")))
c = comparar(pyd, mt, tolerancia="1min")
print("\n===== Réplica frente a Strategy Tester v019 tope, sin simulador (R puro)")
print(c)
p = detalle(c, py, mt)
print("Pares con |ΔR| > 0,10:")
print(p.loc[p.dr.abs() > 0.10, ["fecha", "lado", "r_py", "r_mt5", "sal_py", "sal_mt5", "tipo_py"]].to_string(index=False))
print("Forzadas Python:", list(py.loc[py.forzada, "fecha"].dt.strftime("%Y-%m-%d")))

lv = pd.read_csv("/mnt/project-files/operaciones-live/ops_live.csv", sep=";")
live = pd.DataFrame({"hora": pd.to_datetime(lv.Fecha + " " + lv.Hora, format="%Y.%m.%d %H:%M"), "lado": lv.Lado, "r": lv.R})
live = por_dia(live)
rp = simular(v, tope_pausa=21, desde="2026-10-14", filtro_vol=False)     # en la cuenta corría v017: sin filtro
rp = rp.assign(hora=rp.fecha + ENTRADA)
c2 = comparar(rp, live, tolerancia="1min")
print("\n===== Réplica (sin filtro, como la v017 de la cuenta) frente a la cuenta real FTMO, 14-10 → 06-11")
print(c2)
p2 = detalle(c2, rp.assign(hora=rp.hora), live)
print(p2[["fecha", "lado", "r_py", "r_mt5", "sal_py", "sal_mt5"]].to_string(index=False))
print("Filtro p90 en esos días (réplica):")
print(simular(v, filtro_vol=False, desde="2026-10-14")[["fecha", "pct"]].to_string(index=False))
