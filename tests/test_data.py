import datetime as dt
import unittest
from alert.alert import *


class DataTestCase(unittest.TestCase):

    def test_get_historical_data(self):
        hist = get_historical_data(
            symbol='VN30F1M',
            resolution='1',
            from_ts='1669707900',
            to_ts='1669708905',
        )
        self.assertEqual(type(hist), dict)
        print(hist)

    def test_get_latest_data(self):
        hist = get_latest_data(symbol='VN30F1M')
        self.assertEqual(type(hist), dict)
        print(hist)

    def test_fetch_continuous_data(self):
        fetch_continuous_data(symbol='VN30F1M')


if __name__ == '__main__':
    unittest.main()
