import datetime as dt
import math
import random
import unittest

from lab.backtest import run
from lab.estrategias import month_ranks, turn_of_month, walk_forward_tom, window_stats


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


if __name__ == "__main__":
    unittest.main()
