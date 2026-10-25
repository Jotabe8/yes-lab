import unittest

from lab.btc_intradia import daily_returns, trades


class BtcIntradiaTests(unittest.TestCase):
    def test_follows_first_half_hour(self):
        bars = [
            ("2024-01-01 00:00", 100.0, 101.0),   # r1 +1 %
            ("2024-01-01 12:00", 101.0, 99.0),
            ("2024-01-01 23:00", 100.0, 99.0),    # rN-1 −1 %
            ("2024-01-01 23:30", 100.0, 102.0),   # rN +2 %
            ("2024-01-02 00:00", 100.0, 99.0),    # día incompleto: se descarta
        ]
        days = daily_returns(bars)
        self.assertEqual(list(days), ["2024-01-01"])
        (d, pnl), = trades(days, "principal", 0.05)
        self.assertAlmostEqual(pnl, 2.0 - 0.05)
        # r1 + rN-1 = 0: sin señal en la regla secundaria
        self.assertEqual(trades(days, "secundaria", 0.05), [])


if __name__ == "__main__":
    unittest.main()
