import datetime as dt
import math
import random
import unittest

from lab.backtest import run
from lab.estrategias import (auction_bucket, auction_cycle, fx_momentum_weights, month_end_fixing, month_end_rebalance, month_ranks, run_portfolio, run_weights, turn_of_month,
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


class RebalanceTests(unittest.TestCase):
    def test_short_after_stocks_beat_bonds_only_in_last_sessions(self):
        dates = business_days("2026-01-01", 45)        # enero y febrero completos
        stocks = [100 * 1.002 ** i for i in range(45)]   # las acciones suben
        bonds = [100.0] * 45                             # los bonos no se mueven
        w = month_end_rebalance(dates, stocks, dias=2, umbral=0.0, bonos=bonds)
        _, last = month_ranks(dates)
        held = [last[i + 1] for i in range(len(w) - 1) if w[i] != 0]
        self.assertTrue(held and all(x <= 2 for x in held))
        self.assertTrue(all(x in (0.0, -1.0) for x in w))
        self.assertIn(-1.0, w)

    def test_long_when_stocks_lag(self):
        dates = business_days("2026-01-01", 45)
        stocks = [100 * 0.998 ** i for i in range(45)]
        w = month_end_rebalance(dates, stocks, dias=1, umbral=0.0, bonos=[100.0] * 45)
        self.assertIn(1.0, w)
        self.assertNotIn(-1.0, w)


class AuctionCycleTests(unittest.TestCase):
    def test_bucket_groups_reopenings(self):
        self.assertEqual(auction_bucket("10-Year"), "10")
        self.assertEqual(auction_bucket("9-Year 10-Month"), "10")
        self.assertEqual(auction_bucket("29-Year 11-Month"), "30")
        self.assertEqual(auction_bucket("19-Year 10-Month"), "20")
        self.assertEqual(auction_bucket("1-Year 11-Month"), "2")
        self.assertEqual(auction_bucket("7-Year"), "7")

    def test_short_before_long_after(self):
        dates = business_days("2026-01-05", 20)
        w = auction_cycle(dates, [100.0] * 20, {dates[10]}, antes=3, despues=2)
        # w[t] se aplica a t+1: cortos las sesiones 7, 8 y 9; largos la 11 y la 12
        held = [0.0] + w[:-1]
        self.assertEqual(held[7:10], [-1.0, -1.0, -1.0])
        self.assertEqual(held[10], 0.0)
        self.assertEqual(held[11:13], [1.0, 1.0])
        self.assertEqual(held[13], 0.0)

    def test_filter_is_long_except_before(self):
        dates = business_days("2026-01-05", 20)
        w = auction_cycle(dates, [100.0] * 20, {dates[10]}, antes=2, filtro=True)
        held = [None] + w[:-1]
        self.assertEqual(held[8:10], [0.0, 0.0])
        self.assertEqual(held[5], 1.0)
        self.assertEqual(held[10], 1.0)


class MonthEndFixingTests(unittest.TestCase):
    def test_buys_currencies_only_on_last_day_after_equity_rise(self):
        dates = business_days("2026-01-01", 45)
        equity = [100 * 1.002 ** i for i in range(45)]
        prices = {"EUR": [1.0] * 45, "JPY": [1.0] * 45}
        w = month_end_fixing(dates, prices, equity)
        _, last = month_ranks(dates)
        active = [i for i, x in enumerate(w) if any(x.values())]
        self.assertTrue(active)
        self.assertTrue(all(last[i] == 2 for i in active))        # se aplica al último día
        self.assertTrue(all(w[i]["EUR"] == 0.5 for i in active))

    def test_threshold_and_falling_equity(self):
        dates = business_days("2026-01-01", 45)
        falling = [100 * 0.998 ** i for i in range(45)]
        prices = {"EUR": [1.0] * 45}
        w = month_end_fixing(dates, prices, falling)
        self.assertIn(-1.0, [x["EUR"] for x in w])
        flat = month_end_fixing(dates, prices, falling, umbral=0.5)
        self.assertFalse(any(x["EUR"] for x in flat))


if __name__ == "__main__":
    unittest.main()
