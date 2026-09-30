import unittest
from unittest import mock

from lab import fetch


class FetchParsingTests(unittest.TestCase):
    def test_yahoo_uses_adjclose_and_skips_nulls(self):
        payload = {"chart": {"result": [{
            "timestamp": [1727654400, 1727740800, 1727827200],
            "indicators": {"quote": [{"close": [10, 11, 12]}], "adjclose": [{"adjclose": [9.5, None, 11.5]}]},
        }]}}
        with mock.patch.object(fetch, "_get_json", return_value=payload):
            rows = fetch.fetch_yahoo("SPY", 1)
        self.assertEqual(rows, [{"d": "2024-09-30", "c": 9.5}, {"d": "2024-10-02", "c": 11.5}])

    def test_yahoo_forex_falls_back_to_close(self):
        payload = {"chart": {"result": [{"timestamp": [1727654400], "indicators": {"quote": [{"close": [1.11]}]}}]}}
        with mock.patch.object(fetch, "_get_json", return_value=payload):
            self.assertEqual(fetch.fetch_yahoo("EURUSD=X", 1), [{"d": "2024-09-30", "c": 1.11}])

    def test_binance_paginates(self):
        day = 86_400_000
        first = [[i * day, "0", "0", "0", str(100 + i)] for i in range(1000)]
        second = [[(1000 + i) * day, "0", "0", "0", "5"] for i in range(3)]
        with mock.patch.object(fetch, "_get_json", side_effect=[first, second]):
            rows = fetch.fetch_binance("BTCUSDT", 3)
        self.assertEqual(len(rows), 1003)
        self.assertEqual(rows[0], {"d": "1970-01-01", "c": 100.0})


if __name__ == "__main__":
    unittest.main()
