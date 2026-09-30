import math
import random
import unittest

from lab.backtest import metrics, run, signals, sma, walk_forward


def random_walk(n, seed=1, drift=0.0003, vol=0.01):
    rnd = random.Random(seed)
    p, out = 100.0, []
    for _ in range(n):
        p *= math.exp(drift + vol * rnd.gauss(0, 1))
        out.append(p)
    return out


class BacktestTests(unittest.TestCase):
    def test_sma_values(self):
        self.assertEqual(sma([1, 2, 3, 4], 2), [None, 1.5, 2.5, 3.5])

    def test_always_long_without_costs_matches_buy_and_hold(self):
        closes = random_walk(500)
        res = run(closes, [1] * len(closes), cost_pct=0)
        # entra al cierre del día 0, así que termina igual que comprar y mantener
        self.assertAlmostEqual(res.equity[-1], res.buy_hold[-1], places=6)

    def test_signal_is_applied_next_day(self):
        closes = [100, 110, 121]
        res = run(closes, [1, 0, 0], cost_pct=0)
        # la señal del día 0 captura el movimiento del día 1, no el del día 0
        self.assertAlmostEqual(res.equity[1], 11_000)
        self.assertAlmostEqual(res.equity[2], 11_000)

    def test_costs_reduce_result(self):
        closes = random_walk(800, seed=3)
        sig = signals(closes, "sma", fast=10, slow=30)
        cheap = run(closes, sig, cost_pct=0.0).equity[-1]
        dear = run(closes, sig, cost_pct=0.5).equity[-1]
        self.assertLess(dear, cheap)

    def test_metrics_drawdown(self):
        m = metrics([100, 120, 60, 90], 252)
        self.assertAlmostEqual(m["max_drawdown"], -0.5)

    def test_walk_forward_runs(self):
        closes = random_walk(252 * 6, seed=7)
        wf = walk_forward(closes, "sma", 252, 0.15)
        self.assertEqual(wf["windows"], 3)
        self.assertIn("sharpe", wf["oos"])


if __name__ == "__main__":
    unittest.main()
