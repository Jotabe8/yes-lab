import unittest

import numpy as np

from lab.momentum_cierre import max_dd, nw_ols, trade


def dia(precio=100.0, spread=1.0):
    a = {k: np.full((1, 1440), precio) for k in "ohlc"}
    a["sp"] = np.full((1, 1440), spread)
    return a


class MomentumCierreTests(unittest.TestCase):
    def test_trade_paga_spread_y_deslizamiento(self):
        a = dia()
        # precio plano: largo pierde spread + 2 × 0,2 de deslizamiento; corto pierde lo mismo
        self.assertAlmostEqual(trade(a, 0, 1, 1350, 1375, R=10.0), -0.14)
        self.assertAlmostEqual(trade(a, 0, -1, 1350, 1375, R=10.0), -0.14)
        self.assertAlmostEqual(trade(a, 0, 1, 1350, 1375, R=10.0, k=2.0), -0.28)

    def test_trade_stop(self):
        a = dia()
        a["l"][0, 1360] = 80.0
        self.assertAlmostEqual(trade(a, 0, 1, 1350, 1375, R=10.0, k=0.0), -1.0)

    def test_nw_ols_recupera_pendiente(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=2000)
        b, t, r2 = nw_ols(0.5 * x + rng.normal(size=2000), x)
        self.assertAlmostEqual(b, 0.5, delta=0.05)
        self.assertGreater(t, 10)

    def test_max_dd(self):
        self.assertEqual(max_dd([1, -2, -1, 3]), 3)


if __name__ == "__main__":
    unittest.main()
