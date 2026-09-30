import math
import random
import unittest

from lab import nnfx


def random_bars(n, seed=1, vol=0.006):
    rnd = random.Random(seed)
    p, out = 1.0, []
    for i in range(n):
        o = p
        c = o * math.exp(vol * rnd.gauss(0, 1))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        out.append({"d": f"d{i:05d}", "o": o, "h": h, "l": l, "c": c})
        p = c
    return out


PAIR = nnfx.PORTFOLIO["nzdusd"]


class IndicatorTests(unittest.TestCase):
    def test_alma_of_constant_is_constant(self):
        out = nnfx.alma([2.0] * 60, 50, 6.0, 0.85)
        self.assertIsNone(out[48])
        self.assertAlmostEqual(out[59], 2.0)

    def test_kijun_is_mid_of_range(self):
        out = nnfx.kijun([3, 5, 4], [1, 2, 0], 3)
        self.assertEqual(out[2], 2.5)

    def test_atr_is_mean_true_range(self):
        out = nnfx.atr([2, 3], [1, 1], [1.5, 2.5], 2)
        self.assertAlmostEqual(out[1], (1 + 2) / 2)

    def test_ash_follows_trend(self):
        up = [1 + 0.01 * i for i in range(30)]
        self.assertEqual(nnfx.ash_signal(up, 9, 2)[-1], 1)
        self.assertEqual(nnfx.ash_signal(up[::-1], 9, 2)[-1], -1)

    def test_ssl_uses_previous_bar_averages(self):
        h = [1.1] * 12 + [1.3]
        l = [0.9] * 12 + [1.2]
        c = [1.0] * 12 + [1.25]
        out = nnfx.ssl(h, l, c, 10)
        self.assertEqual(out[11], 0)
        self.assertEqual(out[12], 1)   # cierre por encima de la media de máximos previa


class EngineTests(unittest.TestCase):
    def test_entries_happen_at_next_open(self):
        bars = random_bars(1500, seed=4)
        res = nnfx.backtest(bars, nnfx.Config(), PAIR)
        self.assertGreater(len(res.trades), 20)
        for t in res.trades:
            spread = PAIR.spread_pips * PAIR.pip_size
            self.assertAlmostEqual(t.entry, bars[t.entry_i]["o"] + t.direction * spread / 2)

    def test_stop_loses_about_the_configured_risk(self):
        bars = random_bars(1500, seed=5)
        res = nnfx.backtest(bars, nnfx.Config(risk_pct=0.4), PAIR)
        stops = [t for t in res.trades if t.reason == "sl"]
        self.assertTrue(stops)
        eq = dict(zip(range(len(res.equity)), res.equity))
        for t in stops:
            before = eq[t.entry_i - 1]
            self.assertLess(abs(t.pnl) / before, 0.0045)   # 0.4% + comisión, no el doble

    def test_double_costs_reduce_result(self):
        bars = random_bars(1500, seed=6)
        cheap = nnfx.backtest(bars, nnfx.Config(cost_mult=1), PAIR).equity[-1]
        dear = nnfx.backtest(bars, nnfx.Config(cost_mult=2), PAIR).equity[-1]
        self.assertLess(dear, cheap)

    def test_walk_forward_runs(self):
        bars = random_bars(252 * 5 + 120, seed=7)
        wf = nnfx.walk_forward(bars, PAIR, nnfx.Config())
        self.assertEqual(len(wf["windows"]), 2)
        self.assertIn("ret", wf["windows"][0]["fixed"])


class MonteCarloTests(unittest.TestCase):
    def test_ftmo_path_rules(self):
        self.assertEqual(nnfx.ftmo_path([1.0] * 20)["result"], "PASS")
        self.assertEqual(nnfx.ftmo_path([-5.0])["result"], "FAIL")          # caída diaria del 5%
        self.assertEqual(nnfx.ftmo_path([-2.0] * 6)["result"], "FAIL")      # caída total del 10%
        self.assertEqual(nnfx.ftmo_path([0.0] * 10)["result"], "TIMEOUT")

    def test_monte_carlo_is_reproducible(self):
        daily = [0.5, -0.4, 0.0, 0.0, 0.8]
        a, b = nnfx.monte_carlo(daily, sims=200), nnfx.monte_carlo(daily, sims=200)
        self.assertEqual(a, b)
        self.assertGreater(a["p_pass"], 0)


class DataTests(unittest.TestCase):
    def test_daily_bars_close_is_next_open(self):
        rows = [{"d": "a", "o": 1.0, "h": 1.2, "l": 0.9, "c": 1.0},
                {"d": "b", "o": 1.1, "h": 1.15, "l": 1.05, "c": 1.1},
                {"d": "c", "c": 1.2}]
        bars = nnfx.daily_bars(rows)
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0]["c"], 1.1)


if __name__ == "__main__":
    unittest.main()
