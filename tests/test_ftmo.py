import unittest

from lab import ftmo
from lab.ftmo import DayPnl, Rules, TWO_STEP


def days(*pnls, low=None):
    return [DayPnl(f"d{i}", p, min(0.0, p) if low is None else low, True) for i, p in enumerate(pnls)]


class PhaseTests(unittest.TestCase):
    def test_needs_four_trading_days(self):
        r = ftmo.run_phase(iter(days(6, 5, 0.1, 0.1)), 10, TWO_STEP)
        self.assertEqual((r["result"], r["days"]), ("PASS", 4))

    def test_daily_loss_counts_floating(self):
        # cierra el día en −1% pero llegó a −5% flotante: suspende aunque el balance esté bien
        r = ftmo.run_phase(iter(days(-1, low=-5)), 10, TWO_STEP)
        self.assertEqual(r["result"], "FAIL_DIARIA")

    def test_max_loss_is_static_in_two_step(self):
        # sube un 9% y cae un 9.5%: desde el máximo serían −9.5%, pero el suelo está en −10% del inicial
        seq = days(*([1.5] * 6 + [-1.9] * 5))
        r = ftmo.run_phase(iter(seq), 10, replace_rules(ea_brake=None))
        self.assertEqual(r["result"], "TIMEOUT")

    def test_trailing_floor_in_one_step(self):
        seq = days(*([1.5] * 6 + [-1.9] * 6))
        r = ftmo.run_phase(iter(seq), 10, ftmo.ONE_STEP)
        self.assertEqual(r["result"], "FAIL_TOTAL")

    def test_ea_brake_stops_before_the_firm_limit(self):
        r = ftmo.run_phase(iter(days(*([-0.5] * 20))), 10, TWO_STEP)
        self.assertEqual((r["result"], r["days"]), ("FRENO_EA", 16))

    def test_best_day_rule_delays_the_pass(self):
        r = ftmo.run_phase(iter(days(8, 1, 1, 1, 1, 1, 1, 1, 1)), 10, ftmo.ONE_STEP)
        self.assertEqual(r["days"], 9)   # hasta que el mejor día (8) es ≤ 50% de los días positivos (16)

    def test_challenge_runs_both_phases(self):
        r = ftmo.run_challenge(iter(days(*([1.0] * 20))), TWO_STEP)
        self.assertEqual((r["result"], r["days"]), ("PASS", 15))


class ShutdownTests(unittest.TestCase):
    def test_streak_and_drawdown(self):
        rs = [1, -1, -1, -1, 2, -1]
        self.assertEqual(ftmo._max_streak(rs), 3)
        self.assertEqual(ftmo._max_dd(rs), 3)

    def test_red_flag_on_long_streak(self):
        bands = {"streak": {0.99: 5}, "dd": {0.99: 100}, "cum": {}}
        self.assertEqual(ftmo.red_flag([-1] * 10, bands), 5)
        self.assertIsNone(ftmo.red_flag([1, -1] * 10, bands))


def replace_rules(**kw) -> Rules:
    from dataclasses import replace
    return replace(TWO_STEP, **kw)


if __name__ == "__main__":
    unittest.main()
