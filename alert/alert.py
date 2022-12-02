import datetime as dt
import time

import requests


def get_historical_data(
    symbol: str, resolution: str, from_ts: str, to_ts: str
) -> dict:
    r = requests.get(
        url='https://iboard.ssi.com.vn/dchart/api/history',
        params={
            'symbol': symbol,
            'resolution': resolution,
            'from': from_ts,
            'to': to_ts
        }
    )
    hist = _prep_hist(r.json())

    return hist


def _prep_hist(hist: dict) -> dict:

    if hist['s'] == 'ok':
        hist.pop('s')
    else:
        print(hist)
        return None  # no data

    rename_keys = {
        't': 'timestamp',
        'o': 'open',
        'h': 'high',
        'l': 'low',
        'c': 'close',
        'v': 'vol',
    }
    for old_key, new_key in rename_keys.items():
        hist[new_key] = hist.pop(old_key)

    hist['timestamp'] = [
        dt.datetime.fromtimestamp(int(ele)) for ele in hist['timestamp']
    ]

    for key in ['open', 'high', 'low', 'close']:
        hist[key] = [float(ele) for ele in hist[key]]

    hist['vol'] = [int(ele) for ele in hist['vol']]

    for key in hist.keys():
        if len(hist[key]) == 1:
            hist[key] = hist[key][0]
        elif len(hist[key]) == 0:
            hist[key] = None

    return hist


def get_bar(symbol, closed_at: dt.datetime, timeframe: str = '1m') -> dict:
    if timeframe == '1m':
        from_ts = (closed_at - dt.timedelta(seconds=61)).timestamp()
        print(closed_at - dt.timedelta(seconds=61))
        to_ts = closed_at.timestamp()

        return get_historical_data(
            symbol=symbol, resolution='1', from_ts=from_ts, to_ts=to_ts
        ) | {
            'timeframe': timeframe
        }
    elif timeframe == '5m':
        if closed_at.minute % 5 != 0:
            closed_at += dt.timedelta(seconds=60 * (5 - (closed_at.minute % 5)))

        from_ts = (closed_at - dt.timedelta(seconds=301)).timestamp()
        to_ts = closed_at.timestamp()

        hist = get_historical_data(
            symbol=symbol, resolution='1', from_ts=from_ts, to_ts=to_ts
        ) | {
            'timeframe': timeframe
        }
        hist['timestamp'] = hist['timestamp'][0].replace(second=0)
        hist['open'] = hist['open'][0]
        hist['close'] = hist['close'][-1]
        hist['high'] = max(hist['high'])
        hist['low'] = min(hist['low'])
        hist['vol'] = sum(hist['vol'])
        
        return hist


def get_current_data(symbol: str) -> dict:
    now = dt.datetime.now().replace(microsecond=0)
    curr = get_historical_data(
        symbol=symbol,
        resolution='1',
        from_ts=now.replace(second=0).timestamp(),
        to_ts=now.timestamp()
    )
    if curr is not None:
        curr['timestamp'] = now

    return curr


def fetch_continuous_data(
    symbol: str,
    interval: int = 1,
    verbose: bool = True,
) -> None:
    while True:
        curr = get_current_data(symbol=symbol)
        if curr['close'] is not None:
            if verbose:
                print(f"{symbol} | {curr['timestamp']} | {curr['close']}")
        time.sleep(interval)
    