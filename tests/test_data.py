import datetime as dt
import unittest
from alert.data import *


class DataTestCase(unittest.TestCase):

    def test_get_historical_data(self):
        print(type(
            get_historical_data(
                symbol='VN30F1M',
                resolution='1',
                from_ts='1669707900',
                to_ts='1669708905',
            )
        ))

    def test_get_historical_data_by_datetime(self):
        print(
            get_historical_data_by_datetime(
                symbol='VN30F1M', time=dt.datetime(2022, 11, 29, 14, 45)
            )
        )


if __name__ == '__main__':
    unittest.main()
