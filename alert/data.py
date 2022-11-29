import datetime as dt

import requests

URL = 'https://iboard.ssi.com.vn/dchart/api/history'


def get_historical_data(
    symbol: str, resolution: str, from_ts: str, to_ts: str
) -> dict:
    r = requests.get(
        URL,
        params={
            'symbol': symbol,
            'resolution': resolution,
            'from': from_ts,
            'to': to_ts
        }
    )
    return r.json()


def get_historical_data_by_datetime(symbol: str, time: dt.datetime):
    from_ts = time.replace(second=0).timestamp()
    to_ts = time.replace(second=59).timestamp()

    hist = get_historical_data(
        symbol, resolution='1', from_ts=from_ts, to_ts=to_ts
    )
    if hist['s'] == 'ok':
        hist.pop('s')
    rename_keys = {
        't': 'ts',
        'o': 'open',
        'h': 'high',
        'l': 'low',
        'c': 'close',
        'v': 'vol',
    }
    for old_key, new_key in rename_keys.items():
        hist[new_key] = hist.pop(old_key)
        if len(hist[new_key]) == 1:
            hist[new_key] = hist[new_key][0]
        
    hist['vol'] = int(hist['vol'])
    hist['ts'] = int(hist['ts'])
    
    for key in ['open', 'high', 'low', 'close', 'vol']:
        hist[key] = float(hist[key])
    hist['ts'] = dt.datetime.fromtimestamp(hist['ts'])
    
    return hist
    