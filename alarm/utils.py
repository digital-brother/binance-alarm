import json
import ssl

import websocket
from sentry_sdk import capture_exception

from alarm.models import Coin

previous_close_price = None
previous_candlestick = None
current_prices = None
previous_prices = None


def analize_prices(current_prices, previous_prices):
    threshold = 28150.20
    if previous_prices and current_prices:
        price_broke_threshold_down_top = current_prices <= threshold <= previous_prices
        price_broke_threshold_top_down = previous_prices <= threshold <= current_prices

        if price_broke_threshold_down_top or price_broke_threshold_top_down:
            print('call user')
        else:
            print('continue search prices')


# Websocket

def get_value_s(data):
    return data["s"]


def on_open(ws, currency, interval):
    print(f'Streaming K-line data for {currency} at {interval} intervals...')


def on_message(ws, message, coin_name):
    capture_exception(
        f"Currency: {coin_name}, Current Price: {current_prices}, Previous Price: {previous_prices}")


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("###Close Streaming" + close_msg)


def get_binance_price(currencies, intervals):
    websocket.enableTrace(False)
    sockets = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency, interval in
               zip(currencies, intervals)]

    ws_list = []
    for socket in sockets:
        ws = websocket.create_connection(socket, sslopt={'cert_reqs': ssl.CERT_NONE})
        ws.on_open = on_open
        ws.on_message = on_message
        ws.on_error = on_error
        ws.on_close = on_close
        ws_list.append(ws)

    try:
        while True:
            for ws in ws_list:
                message = ws.recv()
                global previous_close_price
                global previous_candlestick
                global current_prices
                global previous_prices
                # Parse the JSON message
                json_message = json.loads(message)

                # Extract the candlestick data from the JSON message
                candlestick = json_message['k']

                # Extract the close price from the most recent candlestick
                current_close_price = float(candlestick['c'])

                # Update the previous close price, if a previous candlestick is available
                if previous_candlestick is not None:
                    previous_close_price = float(previous_candlestick['c'])

                # Store the current candlestick data for use in the next iteration
                previous_candlestick = candlestick

                # Store the current and previous close prices in a global variable
                current_prices = current_close_price
                previous_prices = previous_close_price
                coin_name = candlestick['s']
                analize_prices(current_prices, previous_prices)
                on_message(ws, message, coin_name)
    except KeyboardInterrupt:
        for i, ws in enumerate(ws_list):
            on_close(ws, '', close_msg=f' {currencies[i]}')
            ws.close()
    except Exception as e:
        print(f'An error occurred: {e}')
