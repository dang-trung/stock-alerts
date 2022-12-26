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

    def test_get_current_data(self):
        hist = get_current_data(symbol='VN30F1M')
        if 9 <= dt.datetime.now().hour <= 14:
            self.assertEqual(type(hist), dict)
            print(hist)
        else:
            print(hist)
            # self.assertEqual(hist, {})  # no data after trading session

    def test_fetch_continuous_data(self):
        fetch_continuous_data(symbol='VN30F1M')

    def test_get_bar(self):
        hist = get_bar(
            symbol='VN30F1M', closed_at=dt.datetime(2022, 12, 1, 14, 30)
        )
        self.assertEqual(hist['timestamp'].minute, 29)
        print(hist)
        hist = get_bar(
            symbol='VN30F1M',
            closed_at=dt.datetime(2022, 12, 1, 14, 30),
            timeframe='5m'
        )
        self.assertEqual(hist['timestamp'].minute, 25)
        print(hist)
        hist = get_bar(
            symbol='VN30F1M',
            closed_at=dt.datetime(2022, 12, 1, 21, 50, 50),
        )
        print(hist)

    def test_get_config(self):
        print(get_config())


if __name__ == '__main__':
    unittest.main()
