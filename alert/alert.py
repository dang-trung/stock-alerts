import csv
import datetime as dt
from pathlib import Path
import time
import tomllib

import requests
from skpy import Skype
from skpy.chat import SkypeSingleChat


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
    elif hist['s'] == 'no_data':
        hist = {'t': [], 'o': [], 'h': [], 'l': [], 'c': [], 'v': []}  # no data

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
        to_ts = closed_at.timestamp()

        return get_historical_data(
            symbol=symbol, resolution='1', from_ts=from_ts, to_ts=to_ts
        ) | {
            'timeframe': timeframe
        }
    elif timeframe == '5m':
        if closed_at.minute % 5 != 0:
            closed_at += dt.timedelta(minutes=(5 - closed_at.minute % 5))

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
    live_alert: bool = True,
) -> None:
    config = get_skype_config()
    sk = Skype(user=config['acc'], pwd=config['pwd'])
    admin = sk.chats[config['admin']]
    targets = [sk.chats[target_user] for target_user in config['target_users']]

    spot_ato = dt.datetime.now().replace(
        hour=9, minute=15, second=0, microsecond=0
    )
    minutes_to_spot_ato = 2

    break_time = dt.datetime.now().replace(
        hour=11, minute=30, second=59, microsecond=0
    )
    minutes_to_break_time = 3

    trading_resume = dt.datetime.now().replace(
        hour=13, minute=0, second=0, microsecond=0
    )
    minutes_to_trading_resume = 2

    atc_open = dt.datetime.now().replace(
        hour=14, minute=30, second=0, microsecond=0
    )
    atc_end = dt.datetime.now().replace(
        hour=14, minute=45, second=0, microsecond=0
    )
    minutes_to_atc_open = 5

    while True:
        try:
            curr = get_current_data(symbol=symbol)
            # checking Spot ATO
            if minutes_to_spot_ato > 0 and (
                curr['timestamp'] >
                spot_ato - dt.timedelta(minutes=minutes_to_spot_ato)
            ):
                send_messages(
                    f"Spot ATO in {minutes_to_spot_ato} min.", targets
                )
                minutes_to_spot_ato -= 1

            # checking Lunchbreak time
            if minutes_to_break_time > 0 and (
                curr['timestamp'] >
                break_time - dt.timedelta(minutes=minutes_to_break_time)
            ):
                send_messages(
                    f"{symbol} | Lunch Break in {minutes_to_break_time} min.",
                    targets
                )
                minutes_to_break_time -= 1

            # Trading resume
            if minutes_to_trading_resume >= 0 and (
                curr['timestamp'] > trading_resume -
                dt.timedelta(minutes=minutes_to_trading_resume)
            ):
                send_messages(
                    f"{symbol} | Trading Resume in {minutes_to_trading_resume} min.",
                    targets
                )
                minutes_to_trading_resume -= 1

            # checking ATC time
            if minutes_to_atc_open > 0 and (
                curr['timestamp'] >
                atc_open - dt.timedelta(minutes=minutes_to_atc_open)
            ):
                send_messages(
                    f"{symbol} | ATC in {minutes_to_atc_open} min.", targets
                )
                minutes_to_atc_open -= 1

            if curr['timestamp'] > atc_end:
                send_messages(
                    f"{symbol} | Market Closed @ {curr['close']}.", targets
                )
                break

            if curr['close'] is not None:

                if verbose:
                    print(f"{symbol} | {curr['timestamp']} | {curr['close']}")

                if live_alert:
                    alerts = get_alerts()
                    for i in range(len(alerts)):
                        alert = alerts[i]
                        cond = False
                        need_update = False

                        if (
                            alert['asset'] == symbol.lower() and
                            alert['type'] == 'price' and
                            alert['active'] == '' and alert['timeframe'] == '1'
                        ):

                            now = dt.datetime.now().replace(microsecond=0)

                            if alert['last_update'] == '':
                                need_update = True
                            else:
                                alert['last_update'] = dt.datetime.strptime(
                                    alert['last_update'], '%Y-%m-%d %H:%M:%S'
                                )
                                if (now - alert['last_update']) > dt.timedelta(
                                    minutes=1
                                ):
                                    need_update = True

                            if need_update:
                                if alert['sign'] == '>':
                                    cond = (
                                        curr['high'] > float(alert['value'])
                                    )
                                elif alert['sign'] == '<':
                                    cond = (curr['low'] < float(alert['value']))
                            if cond:
                                msg = (
                                    f"{alert['asset'].upper()} | "
                                    f"{curr['timestamp'].strftime('%H:%M:%S')} | "
                                    f"Current {curr['close']} | "
                                    f"Crossed {alert['value']} | "
                                    f"{alert['note'].title()}"
                                )
                                send_messages(msg=msg, targets=targets)
                                alert['last_update'] = now
                                alert['alert_times'] = int(
                                    alert['alert_times']
                                ) - 1
                                if alert['alert_times'] == 0:
                                    alert['active'] = 'x'

                            alerts[i] = alert  # rewrite alert

                    with open(
                        Path('alert') / 'resources' / 'alerts.csv',
                        mode='w',
                        newline=''
                    ) as alert_lists:
                        fieldnames = [
                            'asset', 'timeframe', 'type', 'sign', 'value',
                            'note', 'active', 'alert_times', 'last_update'
                        ]
                        writer = csv.DictWriter(
                            alert_lists, fieldnames=fieldnames
                        )
                        writer.writeheader()
                        [writer.writerow(row) for row in alerts]
            time.sleep(interval)
        except Exception as e:
            send_message(msg=str(e), target=admin)
            break


def get_alerts() -> list[dict]:
    with open(
        Path('alert') / 'resources' / 'alerts.csv', mode='r'
    ) as alert_lists:
        alerts = [row for row in csv.DictReader(alert_lists, delimiter=',')]

    return alerts


def send_message(msg: str, target: SkypeSingleChat):
    target.sendMsg(msg, rich=True)


def send_messages(msg: str, targets: list[SkypeSingleChat]):
    [send_message(msg, target) for target in targets]


def get_skype_config():
    with open(Path('alert') / 'resources' / 'skype_config.toml', 'rb') as f:
        config = tomllib.load(f)

    return config