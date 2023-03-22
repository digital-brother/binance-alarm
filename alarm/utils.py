import json
import ssl

import websocket
from sentry_sdk import capture_exception

from alarm.models import Coin

previous_close_price = None
previous_candlestick = None
current_prices = None
previous_prices = None


def get_binance_price_and_analized(currencies, intervals):
    websocket.enableTrace(False)
    sockets = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency, interval in
               zip(currencies, intervals)]

    ws_list = []
    for socket in sockets:
        ws = websocket.create_connection(socket, sslopt={'cert_reqs': ssl.CERT_NONE})
        ws.on_message = on_message
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
                short_coin_name = candlestick['s']
                analize_prices(current_prices, previous_prices)
                on_message(ws, message, short_coin_name)
    except KeyboardInterrupt:
        for i, ws in enumerate(ws_list):
            on_close(ws, '', close_msg=f' {currencies[i]}')
            ws.close()
    except Exception as e:
        capture_exception(e)


def on_message(ws, message, short_coin_name):
    print(
        f"Currency: {short_coin_name}, Current Price: {current_prices}, Previous Price: {previous_prices}")


def on_close(ws, close_status_code, close_msg):
    print("Close Streaming" + close_msg)


def analize_prices(current_prices, previous_prices):
    coin_info = Coin.objects.all()
    for coin in coin_info:
        threshold = coin.threshold

        if previous_prices and current_prices:
            price_broke_threshold_down_top = current_prices >= threshold and current_prices >= previous_prices
            price_broke_threshold_top_down = current_prices <= previous_prices and current_prices <= threshold

            print('threshold', threshold)

            if price_broke_threshold_down_top:
                if previous_prices is not None:
                    print('call user because threshold_down_top')
                    # TODO: should_call_user()
            else:
                print('continue search prices threshold_down_top')
            if price_broke_threshold_top_down:
                if previous_prices is not None:
                    print('call user because threshold_down_top')
                    # TODO: should_call_user()
            else:
                print('continue search prices threshold_top_down')
