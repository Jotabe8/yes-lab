import csv
import datetime as dt
import math
import random
import tempfile
import unittest
from pathlib import Path

from lab.pares import Params, backtest, ols_beta, zscores


def business_days(start, n):
    d, out = dt.date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def write(path, dates, closes):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "close", "low", "high", "vol"])
        prev = closes[0]
        for d, c in zip(dates, closes):
            w.writerow([d, prev, c, min(prev, c), max(prev, c), 1])
            prev = c


class ParesTests(unittest.TestCase):
    def test_ols_beta(self):
        x = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(ols_beta(x, [2 * v + 1 for v in x]), 2.0)

    def test_zscore_ignores_future(self):
        rng = random.Random(1)
        ca = [100 * math.exp(0.01 * i + rng.gauss(0, 0.01)) for i in range(300)]
        cb = [100 * math.exp(0.01 * i + rng.gauss(0, 0.01)) for i in range(300)]
        p = Params()
        z1 = zscores(ca, cb, p)
        z2 = zscores(ca[:250] + [x * 3 for x in ca[250:]], cb, p)
        self.assertEqual(z1[:250], z2[:250])

    def test_mean_reverting_spread_wins_gross_and_costs_hurt(self):
        rng = random.Random(7)
        n = 900
        dates = business_days("2016-01-01", n)
        common, spread, ca, cb = 0.0, 0.0, [], []
        for _ in range(n):
            common += rng.gauss(0, 0.01)
            spread = 0.8 * spread + rng.gauss(0, 0.004)  # AR(1) que revierte rápido
            ca.append(100 * math.exp(common + spread))
            cb.append(100 * math.exp(common))
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "AIDX.csv", dates, ca)
            write(Path(tmp) / "BIDX.csv", dates, cb)
            gross, _ = backtest("A/B", "AIDX", "BIDX", Params(cost_mult=0), Path(tmp))
            net, _ = backtest("A/B", "AIDX", "BIDX", Params(cost_mult=1), Path(tmp))
        self.assertGreater(len(gross), 10)
        self.assertGreater(sum(t.pnl for t in gross), 0)
        self.assertLess(sum(t.pnl for t in net), sum(t.pnl for t in gross))


if __name__ == "__main__":
    unittest.main()
