import tempfile
import unittest
from pathlib import Path

from lab import orb_indices as oi
from lab.us100 import US_HOLIDAYS


class CalendarTests(unittest.TestCase):
    def test_nyse_calendar_matches_the_ea_list(self):
        mine = {h for y in range(2021, 2027) for h in oi.nyse_holidays(y) if h >= "2021-09-01"}
        self.assertEqual(mine, US_HOLIDAYS)

    def test_xetra_has_easter_and_christmas(self):
        self.assertTrue({"2025-04-18", "2025-04-21", "2025-12-24", "2025-12-31"} <= oi.xetra_holidays(2025))

    def test_european_open_moves_an_hour_when_clocks_disagree(self):
        self.assertEqual(oi.eu_shift("2025-03-10"), 60)   # EE. UU. ya en verano, Europa no
        self.assertEqual(oi.eu_shift("2025-10-28"), 60)   # Europa ya en invierno, EE. UU. no
        self.assertEqual(oi.eu_shift("2025-07-01"), 0)
        self.assertEqual(oi.eu_shift("2025-01-10"), 0)


class LoadTests(unittest.TestCase):
    def _csv(self, path, days, spread):
        with open(path, "w") as f:
            f.write("time,open,high,low,close,tick_volume,spread\n")
            for d in days:
                for m in range(60, 23 * 60):
                    f.write(f"{d} {m // 60:02d}:{m % 60:02d},100,101,99,100,5,{spread}\n")

    def test_sources_are_cut_by_date_and_spread_converted(self):
        with tempfile.TemporaryDirectory() as tmp:
            days = [f"2025-02-{d:02d}" for d in range(3, 28) if d % 7 not in (1, 2)]
            self._csv(Path(tmp) / "a.csv", days, 1.5)
            self._csv(Path(tmp) / "b.csv", days, 150)
            manifest = {"US100": [["a.csv", 1.0, None, "2025-02-17"], ["b.csv", 0.01, "2025-02-17", None]]}
            out, sources = oi.load_market("US100", Path(tmp), manifest)
            self.assertEqual([s["file"] for s in sources], ["a.csv", "b.csv"])
            self.assertTrue(all(abs(b.sp - 1.5) < 1e-9 for d in out for b in d.bars))
            self.assertTrue(all(16 * 60 + 30 <= b.m <= 23 * 60 + 30 for d in out for b in d.bars))
            self.assertAlmostEqual(out[0].atr, 2.0)

    def test_ger40_uses_xetra_times(self):
        cfg = oi.config_for("GER40")
        self.assertEqual((cfg.session_start, cfg.flat_time), (600, 1080))
        self.assertIn("2025-12-31", cfg.holidays)


if __name__ == "__main__":
    unittest.main()
