import unittest
from datetime import datetime

from lab.ronda2 import nearest, server, stats


class Ronda2Tests(unittest.TestCase):
    def test_server_is_new_york_plus_7(self):
        self.assertEqual(server(datetime(2023, 7, 3, 9, 30)), "2023-07-03 16:30")
        self.assertEqual(server(datetime(2023, 1, 3, 16, 59)), "2023-01-03 23:59")

    def test_nearest_looks_back_then_forward(self):
        bars = {"2023-01-03 10:00": (1, 1, 0), "2023-01-03 10:07": (2, 2, 0)}
        self.assertEqual(nearest(bars, "2023-01-03 10:03", back=5)[0], "2023-01-03 10:00")
        self.assertEqual(nearest(bars, "2023-01-03 10:05", back=0, forward=3)[0], "2023-01-03 10:07")
        self.assertIsNone(nearest(bars, "2023-01-03 10:05", back=1, forward=1))

    def test_stats(self):
        s = stats([1.0, -1.0, 2.0, 2.0])
        self.assertEqual(s["n"], 4)
        self.assertAlmostEqual(s["media"], 1.0)
        self.assertEqual(s["acierto"], 75)


if __name__ == "__main__":
    unittest.main()
