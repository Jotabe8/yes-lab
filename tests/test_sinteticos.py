import unittest

import numpy as np
import pandas as pd

from metodo.embudo import embudo
from metodo.sinteticos import prueba_motor, velas_paseo


def _velas(n_dias=300, semilla=3):
    """M1 de 9:30 a 11:00 con deriva alcista y volatilidad mayor a la apertura."""
    rng = np.random.default_rng(semilla)
    idx = pd.DatetimeIndex([d + pd.Timedelta(minutes=570 + m)
                            for d in pd.bdate_range("2019-01-01", periods=n_dias) for m in range(90)])
    vol = np.tile(np.linspace(0.002, 0.0005, 90), n_dias)
    ret = rng.normal(0.0002, vol)
    c = 100 * np.exp(np.cumsum(ret))
    o = np.concatenate([[100], c[:-1]]) * np.exp(rng.normal(0, 0.0002, len(c)))
    h = np.maximum(o, c) * (1 + rng.uniform(0, vol))
    l = np.minimum(o, c) * (1 - rng.uniform(0, vol))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx)


def _orb(v, trampa=False):
    """Ruptura del rango de 10 min: señal al cierre por fuera del rango, entrada a la apertura
    siguiente, stop al otro lado del rango (relleno al peor de stop y apertura), salida al cierre
    de la sesión. Simulación exacta: en un paseo aleatorio debe dar R media ≈ 0.
    trampa=True: el fallo real de la prima nocturna (26-10-2026): no recorre el stop vela a vela
    y recorta el resultado final con max(R, -1)."""
    r = []
    for _, d in v.groupby(v.index.date):
        alto, bajo = d.high.iloc[:10].max(), d.low.iloc[:10].min()
        c = d.close.to_numpy()
        fuera = np.flatnonzero((c[10:-1] > alto) | (c[10:-1] < bajo))
        if not len(fuera):
            continue
        i = 10 + fuera[0] + 1                       # vela de entrada
        lado = 1 if c[i - 1] > alto else -1
        ent, stop = d.open.iloc[i], (bajo if lado == 1 else alto)
        riesgo = lado * (ent - stop)
        if riesgo <= 0:
            continue
        final = lado * (c[-1] - ent) / riesgo
        if trampa:
            r.append(max(final, -1.0))
            continue
        tras = d.iloc[i:]
        tocado = np.flatnonzero(((tras.low <= stop) if lado == 1 else (tras.high >= stop)).to_numpy())
        if len(tocado):
            o = tras.open.iloc[tocado[0]]
            salida = min(o, stop) if lado == 1 else max(o, stop)
            r.append(lado * (salida - ent) / riesgo)
        else:
            r.append(final)
    return np.array(r)


class TestPaseo(unittest.TestCase):
    def test_conserva_indice_y_forma(self):
        v = _velas(50)
        s = velas_paseo(v, 1)
        self.assertTrue(s.index.equals(v.index))
        self.assertTrue((s.high >= s[["open", "close"]].max(axis=1) - 1e-9).all())
        self.assertTrue((s.low <= s[["open", "close"]].min(axis=1) + 1e-9).all())
        # sin deriva: el rendimiento medio por minuto del día es 0
        lr = np.log(s.close / s.close.shift()).dropna()
        self.assertLess(abs(lr.mean()), 1e-6)

    def test_motor_correcto_pasa_y_trampa_falla(self):
        v = _velas(150)
        bien = [_orb(velas_paseo(v, s)) for s in range(10)]
        mal = [_orb(velas_paseo(v, s), trampa=True) for s in range(10)]
        self.assertTrue(prueba_motor(bien)["pasa"], prueba_motor(bien))
        self.assertFalse(prueba_motor(mal)["pasa"], prueba_motor(mal))

    def test_puerta_en_embudo(self):
        rng = np.random.default_rng(0)
        fechas = pd.bdate_range("2018-01-01", periods=1500)
        ops = pd.DataFrame({"fecha": fechas, "r_bruto": np.where(rng.random(1500) < 0.4, 2.0, -1.0) + 0.15,
                            "coste_r": 0.03})
        sesgado = embudo(ops, 10, "2022-06-01", paseo=lambda s: np.random.default_rng(s).normal(0.3, 1, 200))
        fila = [p for p in sesgado.puertas if p[0] == "motor en paseo aleatorio"][0]
        self.assertFalse(fila[1])
        self.assertFalse(sesgado.pasa)


if __name__ == "__main__":
    unittest.main()
