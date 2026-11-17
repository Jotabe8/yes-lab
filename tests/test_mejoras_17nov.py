import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from metodo.embudo import embudo, t_agrupado, t_stat
from metodo.sinteticos import prueba_motor, sin_fuga, velas_nulo
from tests.test_sinteticos import _orb, _velas


class TestTAgrupado(unittest.TestCase):
    def test_un_grupo_por_op_es_t_normal(self):
        r = np.random.default_rng(0).normal(0.1, 1, 500)
        self.assertAlmostEqual(t_agrupado(r, np.arange(500)), t_stat(r), delta=0.05 * abs(t_stat(r)))

    def test_mercados_copiados_no_suman_t(self):
        r = np.random.default_rng(1).normal(0.1, 1, 400)
        fechas = np.arange(400)
        r4, g4 = np.tile(r, 4), np.tile(fechas, 4)        # el mismo resultado en 4 "mercados"
        self.assertAlmostEqual(t_stat(r4) / t_stat(r), 2.0, delta=0.05)
        self.assertAlmostEqual(t_agrupado(r4, g4), t_agrupado(r, fechas), delta=0.05)

    def test_embudo_usa_t_agrupado(self):
        rng = np.random.default_rng(2)
        f = pd.bdate_range("2011-01-03", periods=1500)
        r = np.where(rng.random(1500) < 0.6, -1.0, rng.exponential(1.8, 1500))
        o = pd.concat([pd.DataFrame({"fecha": f, "r_bruto": r, "coste_r": 0.03})] * 4)
        txt = str(embudo(o, 10, "2023-01-01", agrupar="W"))
        self.assertIn("por op", txt)


class TestLibro(unittest.TestCase):
    def test_cuenta_reglas_distintas_y_sube_n(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["LIBRO_PRUEBAS_DIR"] = d
            try:
                from metodo import libro_pruebas as L
                f = pd.bdate_range("2018-01-01", periods=300)
                o = pd.DataFrame({"fecha": f, "r_bruto": np.r_[np.ones(150), -np.ones(150)], "coste_r": 0.01})
                for k in range(12):
                    L.apuntar("prueba", {"k": k}, o)
                L.apuntar("prueba", {"k": 0}, o)          # repetida: no cuenta
                self.assertEqual(L.contar("prueba"), 12)
                self.assertEqual(L.matriz("prueba").shape, (300, 12))
                res = embudo(o, 3, "2019-01-01", familia="prueba", regla={"k": 99})
                self.assertIn("n_pruebas 3 → 13", str(res))
            finally:
                del os.environ["LIBRO_PRUEBAS_DIR"]


class TestNulos(unittest.TestCase):
    def test_garch_y_regimen_son_martingala_para_el_orb(self):
        v = _velas(n_dias=400)
        for tipo in ("garch", "regimen"):
            r = [_orb(velas_nulo(v, s, tipo)) for s in range(6)]
            self.assertTrue(prueba_motor(r)["pasa"], tipo)

    def test_garch_agrupa_la_volatilidad(self):
        v = velas_nulo(_velas(n_dias=400), 0, "garch")
        rango = (np.log(v.high / v.low)).groupby(v.index.date).mean()
        self.assertGreater(rango.autocorr(1), 0.2)

    def test_sin_fuga(self):
        v = _velas(n_dias=60)
        buena = lambda x: (x.close > x.close.rolling(20).mean()).astype(float).where(x.close.rolling(20).mean().notna())
        mala = lambda x: (x.close.shift(-1) > x.close).astype(float)      # mira la vela siguiente
        self.assertTrue(sin_fuga(buena, v)["pasa"])
        self.assertFalse(sin_fuga(mala, v)["pasa"])


if __name__ == "__main__":
    unittest.main()
