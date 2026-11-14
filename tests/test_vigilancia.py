import unittest

import numpy as np
import pandas as pd

from metodo.vigilancia import alerta_ejecucion, cruce, limites_sprt, sprt


def _r_orb(n, media, rng):
    """R con forma parecida al ORB v018: ~31 % de aciertos, cola derecha larga, σ ≈ 1,8."""
    gana = rng.random(n) < 0.31
    r = np.where(gana, rng.exponential(3.0, n) + 0.3, -1.0)
    return (r - r.mean()) / r.std() * 1.8 + media


class TestSPRT(unittest.TestCase):
    def test_limites_en_suma_de_r(self):
        lo, hi, p = limites_sprt()
        self.assertAlmostEqual(lo, -42.1, delta=0.1)
        self.assertAlmostEqual(hi, 74.9, delta=0.1)
        self.assertAlmostEqual(p, 0.06)

    def test_potencia_como_la_auditoria(self):
        # Auditoría v4: con edge +0,12 para ~18 % y confirma ~76 %; sin edge para ~92 %.
        rng = np.random.default_rng(3)
        res = {}
        for mu in (0.12, 0.0):
            est = [sprt(_r_orb(3000, mu, rng)).estado for _ in range(1500)]
            res[mu] = (est.count("parar") / 1500, est.count("confirmado") / 1500)
        self.assertLess(res[0.12][0], 0.25)
        self.assertGreater(res[0.12][1], 0.68)
        self.assertGreater(res[0.0][0], 0.85)

    def test_decision_definitiva(self):
        r = np.r_[np.full(50, -1.0), np.full(500, 2.0)]  # cae primero bajo el límite y luego se recupera
        e = sprt(r)
        self.assertEqual(e.estado, "parar")
        self.assertLess(e.decidido_en, 60)

    def test_pocas_ops_sigue(self):
        self.assertEqual(sprt([-1.0] * 30).estado, "seguir")


class TestCruce(unittest.TestCase):
    def test_marca_fallos(self):
        f = pd.bdate_range("2026-01-05", periods=5)
        replica = pd.DataFrame({"fecha": f, "lado": ["largo", "corto", "largo", "largo", "corto"],
                                "R": [1.0, -1.0, 0.5, 2.0, -1.0]})
        real = pd.DataFrame({"fecha": f[[0, 1, 2, 4]], "lado": ["largo", "largo", "largo", "corto"],
                             "R": [0.95, -1.0, 1.2, -0.99]})
        m = cruce(real, replica)
        self.assertEqual(m["estado"].tolist(), ["ok", "lado", "r", "falta_real", "ok"])
        alerta, tasa = alerta_ejecucion(m)
        self.assertTrue(alerta)
        self.assertAlmostEqual(tasa, 0.6)


if __name__ == "__main__":
    unittest.main()
