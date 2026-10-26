import unittest

from lab import us100
from lab.us100 import Bar, Day, OrbConfig, VwapConfig

OPEN = 16 * 60 + 30


def flat_day(d, price=20000.0, start=OPEN - 30, end=23 * 60, sp=100, atr=100.0):
    bars = [Bar(m, price, price + 1, price - 1, price, 10, sp) for m in range(start, end)]
    return Day(d, bars, atr)


def set_bar(day, m, o, h, l, c, v=10):
    i = next(i for i, b in enumerate(day.bars) if b.m == m)
    day.bars[i] = Bar(m, o, h, l, c, v, day.bars[i].sp)


def trend_after_open(day, step):
    """Mueve el precio `step` puntos por minuto desde la apertura (la vela del rango toma la dirección)."""
    p = day.bars[0].o
    for i, b in enumerate(day.bars):
        if b.m >= OPEN:
            o, p = p, p + step
            day.bars[i] = Bar(b.m, o, max(o, p) + 0.5, min(o, p) - 0.5, p, b.v, b.sp)


class RiskTests(unittest.TestCase):
    def test_lots_risk_what_is_configured(self):
        lots = us100.lots_for(100_000, 0.5, 47.3, 20000, 6)
        self.assertLessEqual(lots * 47.3, 500)
        self.assertGreater(lots * 47.3, 500 - 47.3 * 0.01)

    def test_notional_cap_limits_lots(self):
        self.assertAlmostEqual(us100.lots_for(100_000, 2.0, 10, 20000, 6), 30.0)

    def test_stop_loss_is_one_r(self):
        day = flat_day("2025-03-04")
        trend_after_open(day, 2.0)          # rango alcista → largo
        for i, b in enumerate(day.bars):    # a las 17:00 cae de golpe por debajo del stop (15 puntos)
            if b.m >= 17 * 60:
                day.bars[i] = Bar(b.m, b.o - 100, b.h - 100, b.l - 100, b.c - 100, b.v, b.sp)
        res = us100.backtest_orb([day], OrbConfig(slippage_pts=0))
        self.assertEqual(len(res.trades), 1)
        t = res.trades[0]
        self.assertEqual((t.side, t.reason), (1, "SL"))
        self.assertLess(t.r, -0.99)


class OrbTests(unittest.TestCase):
    def test_bullish_range_goes_long_and_closes_at_flat_time(self):
        day = flat_day("2025-03-04")
        trend_after_open(day, 0.05)
        res = us100.backtest_orb([day], OrbConfig())
        self.assertEqual(len(res.trades), 1)
        t = res.trades[0]
        self.assertEqual((t.side, t.reason), (1, "EA"))
        self.assertAlmostEqual(t.entry, day.bars[OPEN + 10 - day.bars[0].m].o + 1.0 + 0.1)
        self.assertGreater(t.pnl, 0)

    def test_bearish_range_goes_short(self):
        day = flat_day("2025-03-04")
        trend_after_open(day, -0.05)
        self.assertEqual(us100.backtest_orb([day], OrbConfig()).trades[0].side, -1)

    def test_doji_and_holiday_do_not_trade(self):
        doji = flat_day("2025-03-04")
        holiday = flat_day("2025-07-04")
        trend_after_open(holiday, 1.0)
        self.assertEqual(us100.backtest_orb([doji, holiday], OrbConfig()).trades, [])

    def test_short_stop_uses_ask(self):
        day = flat_day("2025-03-04", sp=500)       # spread de 5 puntos
        trend_after_open(day, -0.5)
        bid_in = next(b.o for b in day.bars if b.m == OPEN + 10)
        i = next(i for i, b in enumerate(day.bars) if b.m == 17 * 60)
        b = day.bars[i]
        # el bid sube 11 puntos sobre la entrada: con 5 de spread el ask pasa del stop de 15
        day.bars[i] = Bar(b.m, b.o, bid_in + 11, b.l, b.c, b.v, b.sp)
        t = us100.backtest_orb([day], OrbConfig(slippage_pts=0)).trades[0]
        self.assertEqual(t.reason, "SL")

    def test_daily_atr_uses_previous_day(self):
        days = [flat_day(f"2025-01-{i:02d}", atr=None) for i in range(1, 17)]
        days[15].bars[0] = Bar(days[15].bars[0].m, 20000, 25000, 20000, 20000, 1, 100)
        us100.add_daily_atr(days)
        self.assertAlmostEqual(days[15].atr, 2.0)


class VwapTests(unittest.TestCase):
    def test_adx_of_flat_series_is_zero(self):
        self.assertEqual(us100.adx_mt5([1] * 20, [1] * 20, [1] * 20, 14)[-1], 0.0)

    def test_m5_groups_minutes(self):
        bars5 = us100.m5_bars(flat_day("2025-03-04", start=OPEN, end=OPEN + 10))
        self.assertEqual([b.m for b, _, _ in bars5], [OPEN, OPEN + 5])

    def test_drop_below_band_with_reversal_buys_back_to_vwap(self):
        day = flat_day("2025-03-04", start=OPEN - 120, end=19 * 60)
        # 17:10 cae 60 puntos, 17:15 vela de giro alcista, 17:20 vuelve por encima del VWAP
        for m in range(OPEN + 40, OPEN + 45):
            set_bar(day, m, 19940, 19941, 19939, 19940)
        set_bar(day, OPEN + 45, 19940, 19945, 19939, 19942)
        set_bar(day, OPEN + 49, 19942, 19945, 19941, 19944)
        for m in range(OPEN + 50, OPEN + 60):
            set_bar(day, m, 19944, 20010, 19943, 20005)
        res = us100.backtest_vwap([day], VwapConfig(use_adx=False))
        self.assertTrue(res.trades)
        t = res.trades[0]
        self.assertEqual((t.side, t.reason), (1, "TP"))
        self.assertGreater(t.pnl, 0)


class HelperTests(unittest.TestCase):
    def test_daily_returns_start_from_capital(self):
        res = us100.Result(["a", "b"], [101.0, 101.0])
        self.assertEqual([round(x, 6) for x in us100.daily_returns(res, 100.0)], [1.0, 0.0])

    def test_chain_rebases_windows(self):
        a, b = us100.Result(["a"], [110.0]), us100.Result(["b"], [110.0])
        self.assertAlmostEqual(us100.chain([a, b], 100.0)[-1], 121.0)


if __name__ == "__main__":
    unittest.main()
