import unittest

import numpy as np

from metodo.rapido import K_INI, K_RANGO_FIN, K_SALIDA, atr_sesion, orb_r, orb_r_python, placebo_direccion


def _dias(n=60, semilla=0, deriva=0.0):
    """Matriz sintética días × 600 minutos × (o, h, l, c, spr) de paseo aleatorio."""
    rng = np.random.default_rng(semilla)
    x = np.full((n, 600, 5), np.nan)
    for i in range(n):
        p = 100 + np.cumsum(rng.normal(deriva, 0.05, 601))
        o, c = p[:-1], p[1:]
        x[i, :, 0], x[i, :, 3] = o, c
        x[i, :, 1] = np.maximum(o, c) + 0.01
        x[i, :, 2] = np.minimum(o, c) - 0.01
        x[i, :, 4] = 0.02
    return x


class TestRapido(unittest.TestCase):
    def test_numba_igual_que_python(self):
        x = _dias(80)
        atr = atr_sesion(x)
        for lados in (np.zeros(80, np.int8), np.where(np.arange(80) % 2, 1, -1).astype(np.int8)):
            np.testing.assert_allclose(orb_r(x, atr, lados), orb_r_python(x, atr, lados), equal_nan=True)

    def test_atr_solo_usa_dias_anteriores(self):
        x = _dias(30)
        a1 = atr_sesion(x)
        x2 = x.copy(); x2[20, K_INI:, 1] += 50  # día 20 enorme: no puede cambiar su propio ATR
        a2 = atr_sesion(x2)
        self.assertEqual(a1[20], a2[20])
        self.assertTrue(np.isnan(a1[:14]).all())
        self.assertNotEqual(a1[21], a2[21])

    def test_festivo_vacio_no_cuenta_como_cero(self):
        x = _dias(40)
        a1 = atr_sesion(x)
        x[25] = np.nan  # festivo
        a2 = atr_sesion(x)
        self.assertTrue(np.isnan(a2[25]))
        self.assertAlmostEqual(a2[26], a1[25])  # el día siguiente usa los mismos 14 días con sesión

    def test_stop_y_salida(self):
        x = _dias(1)
        x[0, K_INI:K_RANGO_FIN, :4] = [[100, 100.5, 99.9, 100.4]] * 10  # vela alcista → largo
        x[0, K_INI, 0] = 100.0
        x[0, K_RANGO_FIN:, :4] = 101.0  # sin tocar el stop
        x[0, K_SALIDA, 0] = 102.0
        r = orb_r(x, np.array([10.0]), np.zeros(1, np.int8))[0]
        self.assertAlmostEqual(r, (102.0 - 101.0) / 1.5)  # stop a 0,15 × 10

    def test_paseo_aleatorio_sin_ventaja(self):
        x = _dias(1500, semilla=3)
        r = orb_r(x, atr_sesion(x), np.zeros(len(x), np.int8))
        r = r[np.isfinite(r)]
        self.assertLess(abs(r.mean() / r.std() * np.sqrt(len(r))), 3.0)
        self.assertEqual(len(placebo_direccion(x, atr_sesion(x), replicas=5)), 5)


if __name__ == "__main__":
    unittest.main()
