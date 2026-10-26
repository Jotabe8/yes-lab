import csv
import datetime as dt
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from lab import forward
from lab.us100 import Bar, Day, OrbConfig, backtest_orb

OPEN = 16 * 60 + 30
DEAL_FIELDS = ["ticket", "order", "time", "time_msc", "type", "entry", "magic", "position_id", "reason",
               "volume", "price", "commission", "swap", "profit", "fee", "symbol", "comment"]


def epoch(d, hhmmss):
    return int(dt.datetime.fromisoformat(f"{d} {hhmmss}").replace(tzinfo=dt.timezone.utc).timestamp())


def trend_day(d, step, price=20000.0, sp=100):
    """Plano hasta la apertura y después `step` puntos por minuto: rango con dirección clara."""
    bars, p = [], price
    for m in range(OPEN - 30, 23 * 60):
        o = p
        if m >= OPEN:
            p += step
        bars.append(Bar(m, o, max(o, p) + 0.5, min(o, p) - 0.5, p, 10, sp))
    return Day(d, bars, 100.0)


def write_deals(path, deals):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DEAL_FIELDS)
        w.writeheader()
        for i, x in enumerate(deals):
            w.writerow({"ticket": i + 1, "time_msc": x["time"] * 1000, "magic": 16, "swap": 0, "fee": 0,
                        "commission": 0, "symbol": "US100.cash", "comment": "", **x})


class LoadLiveTests(unittest.TestCase):
    def test_groups_deals_into_positions_with_sl(self):
        tmp = Path(tempfile.mkdtemp())
        write_deals(tmp / "deals.csv", [
            {"order": 11, "time": epoch("2026-10-05", "16:40:01"), "type": 0, "entry": 0, "position_id": 11,
             "reason": 3, "volume": 3.3, "price": 20021.5, "profit": 0},
            {"order": 12, "time": epoch("2026-10-05", "17:02:10"), "type": 1, "entry": 1, "position_id": 11,
             "reason": 4, "volume": 3.3, "price": 20006.0, "profit": -51.15},
            {"order": 13, "time": epoch("2026-10-06", "16:40:00"), "type": 1, "entry": 0, "position_id": 13,
             "reason": 3, "volume": 2.0, "price": 19900.0, "profit": 0},
        ])
        with open(tmp / "orders.csv", "w", newline="") as f:
            f.write("ticket,sl\n11,20006.5\n13,19915\n")
        live = forward.load_live(tmp / "deals.csv", tmp / "orders.csv")
        self.assertEqual(len(live), 1)                      # la del día 6 sigue abierta
        t = live[0]
        self.assertEqual((t.d, t.side, t.t_in, t.exit_reason, t.sl), ("2026-10-05", 1, "16:40:01", "SL", 20006.5))
        self.assertAlmostEqual(t.pnl, -51.15)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.cfg = OrbConfig(capital=100_000)
        self.days = [trend_day("2026-10-05", 2.0), trend_day("2026-10-06", -2.0), trend_day("2026-10-07", 0.0)]

    def test_matching_trade_slippage_and_r(self):
        m = backtest_orb(self.days, replace(self.cfg, slippage_pts=0)).trades[0]
        live = [forward.LiveTrade(1, "2026-10-05", 1, m.lots, "16:40:01", "22:30:00", m.entry + 0.8,
                                  m.exit - 0.3, m.entry + 0.8 - m.stop_dist, (m.exit - m.entry - 1.1) * m.lots, 0.0, "EA")]
        rows = forward.compare(self.days, live, self.cfg)
        r = rows[0]
        self.assertAlmostEqual(r["slip_in"], 0.8)
        self.assertAlmostEqual(r["slip_out"], 0.3)
        self.assertAlmostEqual(r["live_r"], (m.exit - m.entry - 1.1) / m.stop_dist)
        s = forward.summary(rows)
        self.assertEqual((s["model_trades"], s["same_side"], s["missed"]), (2, 1, ["2026-10-06"]))
        self.assertIn("doji", rows[2]["reason"])

    def test_report_mentions_missed_day_and_log_reason(self):
        logs = {"2026-10-06": ["16:40:00.1 ORB_US100_v016 (US100.cash,M5) Día descartado: filtro de noticias"]}
        rows = forward.compare(self.days, [], self.cfg, logs=logs)
        text = forward.render(rows, forward.summary(rows), "2026-10-05", "2026-10-07", self.cfg)
        self.assertIn("el EA no abrió; log:", text)
        self.assertIn("filtro de noticias", text)

    def test_normalize_m1_accepts_epoch_times(self):
        tmp = Path(tempfile.mkdtemp()) / "m1.csv"
        tmp.write_text(f"time,open,high,low,close,tick_volume,spread,real_volume\n"
                       f"{epoch('2026-10-05', '16:30:00')},1,2,0.5,1.5,10,100,0\n")
        with open(forward.normalize_m1(tmp)) as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["time"], "2026-10-05 16:30")


if __name__ == "__main__":
    unittest.main()
