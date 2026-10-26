import unittest

import numpy as np
import pandas as pd

from metodo.embudo import embudo, t_requerido


def _ops(media, n=1500, semilla=1):
    rng = np.random.default_rng(semilla)
    fechas = pd.bdate_range("2018-01-01", periods=n)
    r = np.where(rng.random(n) < 0.4, 2.0, -1.0) + media - 0.2
    return pd.DataFrame({"fecha": fechas, "r_bruto": r, "coste_r": 0.03})


class TestEmbudo(unittest.TestCase):
    def test_t_requerido_crece_con_pruebas(self):
        self.assertTrue(1.6 < t_requerido(1) < 1.7)
        self.assertGreater(t_requerido(100), t_requerido(10))

    def test_sin_edge_se_descarta(self):
        self.assertFalse(embudo(_ops(0.0), n_pruebas=10, corte_oos="2022-06-01").pasa)

    def test_con_edge_claro_pasa(self):
        res = embudo(_ops(0.35), n_pruebas=10, corte_oos="2022-06-01")
        self.assertTrue(res.pasa, str(res))


if __name__ == "__main__":
    unittest.main()
