import json
import ssl

import websocket
from sentry_sdk import capture_exception
from alarm.models import Coin, Candle


def get_binance_price_and_analized(currencies, intervals):
    websocket.enableTrace(False)
    sockets_urls = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency, interval in
                    zip(currencies, intervals)]

    socket_list = []
    for socket_url in sockets_urls:
        socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
        socket.on_message = feedback_message_from_websocket
        socket.on_close = close_streaming_message_from_websocket
        socket_list.append(socket)

    try:
        while True:
            for ws in socket_list:
                message = ws.recv()
                # Parse the JSON message
                json_message = json.loads(message)

                # Extract the current candle data from the JSON message
                current_candle = json_message['k']

                # Extract the high price from the current candle
                current_high_price = float(current_candle['h'])

                # Extract the high price from the current candle
                current_low_price = float(current_candle['l'])

                # Store the current candle data for use in the next iteration
                candles = Candle.objects.all()
                for candle in candles:
                    coin = candle.coin

                    # Update or create the candle
                    Candle.objects.update_or_create(
                        coin=coin,
                        defaults={
                            'last_high_price': current_high_price,
                            'last_low_price': current_low_price,
                        },
                    )

                # Extract the current high price and current low price to analyze prices function
                analyze_prices(current_high_price, current_low_price)
                feedback_message_from_websocket(current_high_price, current_low_price)
    except KeyboardInterrupt:
        # handle the KeyboardInterrupt exception
        for i, ws in enumerate(socket_list):
            close_streaming_message_from_websocket(ws, '', close_msg=f' {currencies[i]}')
            ws.close()
    except ValueError as err:
        # handle the ValueError exception
        capture_exception(err)
    except KeyError as err:
        # handle the KeyError exception
        capture_exception(err)


def feedback_message_from_websocket(current_high_price, current_low_price):
    print(
        f"High Price: {current_high_price}, Low Price: {current_low_price}")


def close_streaming_message_from_websocket(ws, close_status_code, close_msg):
    print("Close Streaming" + close_msg)


def analyze_prices(high_price, low_price):
    # Get the last high and low price, if a candle is available
    last_candle = Candle.objects.last()
    if last_candle:
        last_high_price = last_candle.last_high_price
        last_low_price = last_candle.last_low_price

        # Get the threshold for the coin
        coin = Coin.objects.last()
        if coin:
            threshold = coin.threshold
            # Check if the current price is within the threshold
            if min(last_low_price, low_price) <= threshold <= max(last_high_price, high_price):
                # TODO: Put call in queue
                pass
