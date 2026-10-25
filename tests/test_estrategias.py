import datetime as dt
import math
import random
import unittest

from lab.backtest import run
from lab.estrategias import (fx_momentum_weights, month_ranks, run_portfolio, run_weights, turn_of_month,
                             vol_managed, walk_forward_tom, walk_forward_weights, window_stats)


def business_days(start, n):
    d, out = dt.date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


class TurnOfMonthTests(unittest.TestCase):
    def test_month_ranks(self):
        dates = ["2026-01-29", "2026-01-30", "2026-02-02", "2026-02-03", "2026-02-04"]
        first, last = month_ranks(dates)
        self.assertEqual(first, [1, 2, 1, 2, 3])
        self.assertEqual(last, [2, 1, 3, 2, 1])

    def test_signal_holds_last_and_first_sessions(self):
        dates = business_days("2026-01-01", 60)
        sig = turn_of_month(dates, antes=1, despues=2)
        # el día t+1 cae en la ventana si es la última sesión del mes o una de las 2 primeras
        held = [dates[i + 1] for i in range(len(dates) - 1) if sig[i]]
        self.assertIn("2026-01-30", held)   # última sesión de enero
        self.assertIn("2026-02-02", held)
        self.assertIn("2026-02-03", held)
        self.assertNotIn("2026-02-04", held)
        self.assertNotIn("2026-01-29", held)

    def test_strategy_only_earns_window_returns(self):
        dates = business_days("2026-01-01", 45)
        closes = [100.0]
        for d in dates[1:]:
            closes.append(closes[-1] * (1.01 if d == "2026-01-30" else 1.0))
        res = run(closes, turn_of_month(dates, antes=1, despues=1), cost_pct=0)
        self.assertAlmostEqual(res.equity[-1], 10_100)

    def test_walk_forward_runs(self):
        rnd = random.Random(2)
        dates = business_days("2018-01-01", 252 * 5)
        p, closes = 100.0, []
        for _ in dates:
            p *= math.exp(0.0003 + 0.01 * rnd.gauss(0, 1))
            closes.append(p)
        wf = walk_forward_tom(dates, closes, 252, 0.05)
        self.assertEqual(wf["windows"], 2)
        self.assertGreater(window_stats(closes, turn_of_month(dates))["exposicion"], 0.1)


def walk(n, seed, vol=0.01):
    rnd = random.Random(seed)
    p, out = 100.0, []
    for _ in range(n):
        p *= math.exp(0.0002 + vol * rnd.gauss(0, 1))
        out.append(p)
    return out


class VolManagedTests(unittest.TestCase):
    def test_full_weight_without_costs_is_buy_and_hold(self):
        closes = walk(300, 4)
        eq = run_weights(closes, [1.0] * len(closes), cost_pct=0)
        self.assertAlmostEqual(eq[-1] / eq[0], closes[-1] / closes[0])

    def test_weight_is_capped_and_changes_only_at_month_end(self):
        dates = business_days("2020-01-01", 300)
        closes = walk(300, 5, vol=0.002)    # volatilidad muy baja: el peso choca con el tope
        w = vol_managed(dates, closes, 252, objetivo=0.12, dias=21, tope=1.0)
        self.assertTrue(all(0 <= x <= 1.0 for x in w))
        _, last = month_ranks(dates)
        for i in range(1, len(w)):
            if w[i] != w[i - 1]:
                self.assertEqual(last[i], 1)

    def test_walk_forward_runs(self):
        dates = business_days("2018-01-01", 252 * 5)
        closes = walk(len(dates), 6)
        build = lambda d, c, **p: vol_managed(d, c, 252, **p)
        wf = walk_forward_weights(dates, closes, 252, 0.05, build, [{"objetivo": 0.1, "dias": 21}])
        self.assertEqual(wf["windows"], 2)


class FxMomentumTests(unittest.TestCase):
    def test_weights_are_dollar_neutral_and_long_winners(self):
        dates = business_days("2020-01-01", 120)
        prices = {c: [100 * (1 + g) ** i for i in range(120)]
                  for c, g in zip("ABCDEF", (0.002, 0.001, 0.0, -0.001, -0.002, 0.0005))}
        w = fx_momentum_weights(dates, prices, meses=1, k=2)
        self.assertAlmostEqual(sum(w[-1].values()), 0.0)
        self.assertAlmostEqual(sum(abs(x) for x in w[-1].values()), 1.0)
        self.assertGreater(w[-1]["A"], 0)
        self.assertLess(w[-1]["E"], 0)
        # con tendencias constantes la cartera gana
        eq = run_portfolio(prices, w, cost_pct=0)
        self.assertGreater(eq[-1], eq[0])


if __name__ == "__main__":
    unittest.main()
