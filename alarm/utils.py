from alarm.models import Coin, Candle
import websocket
import json
import ssl


def connect_binance_socket(currencies, intervals):
    websocket.enableTrace(False)
    socket_urls = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency, interval in
                   zip(currencies, intervals)]

    sockets = []
    for socket_url in socket_urls:
        socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
        socket.on_message = feedback_message_from_websocket
        socket.on_close = close_streaming_message_from_websocket
        sockets.append(socket)

    return sockets


def process_binance_messages(sockets):
    try:
        while True:
            for socket in sockets:
                message = socket.recv()
                handle_binance_message(message)
    except KeyboardInterrupt:
        close_binance_sockets(sockets)
    except (ValueError, KeyError) as err:
        print(err)


def parse_binance_message(message):
    """
    Parse a Binance WebSocket message and return the relevant data.

    :param message: The WebSocket message to parse.
    :return: A tuple containing the current candle high price, current candle low price, and coin abbreviation.
    """
    json_message = json.loads(message)
    current_candle = json_message['k']
    current_candle_high_price = float(current_candle['h'])
    current_candle_low_price = float(current_candle['l'])
    coin_symbol = current_candle['s']
    coin_abbreviation = coin_symbol.lower()

    return current_candle_high_price, current_candle_low_price, coin_abbreviation


def handle_binance_message(message):
    """
    Handle a Binance WebSocket message.

    :param message: The WebSocket message to handle.
    """
    try:
        # Parse the message to extract relevant data
        current_candle_high_price, current_candle_low_price, coin_abbreviation = parse_binance_message(message)

        # Get the coin from the database
        coin = Coin.objects.filter(coin_abbreviation=coin_abbreviation).first()
        if not coin:
            # There is no coin with this abbreviation in the database
            # TODO: Handle this case appropriately
            return

        # Update or create the candles for the coin
        Candle.objects.update_or_create(
            coin=coin,
            defaults={
                'last_high_price': current_candle_high_price,
                'last_low_price': current_candle_low_price,
            },
        )

        # Send prices to analyze and send feedback messages
        threshold = coin.threshold
        coin_last_candle = Candle.objects.filter(coin=coin).last()
        if not coin_last_candle:
            # There are no candles for this coin yet
            # TODO: Handle this case appropriately
            return
        last_high_price = coin_last_candle.last_high_price
        last_low_price = coin_last_candle.last_low_price

        analyze_prices(current_candle_high_price, current_candle_low_price, coin_abbreviation, threshold,
                       last_high_price,
                       last_low_price)

        feedback_message_from_websocket(coin_abbreviation, current_candle_high_price, threshold,
                                        current_candle_low_price)

    except (KeyError, ValueError, TypeError) as e:
        # An error occurred while parsing the message
        # TODO: Handle this case appropriately
        pass


def close_binance_sockets(sockets):
    for i, socket in enumerate(sockets):
        close_streaming_message_from_websocket(socket, '', close_msg=f'Close')
        socket.close()


def feedback_message_from_websocket(coin_abbreviation, current_candle_high_price, threshold, current_candle_low_price):
    print(
        f"Coin Abbreviation: {coin_abbreviation}, High Price: {current_candle_high_price}, Threshold: {threshold}, "
        f"Low Price: {current_candle_low_price}")


def close_streaming_message_from_websocket(ws, close_status_code, close_msg):
    print("Close Streaming" + close_msg)


def analyze_prices(current_candle_high_price, current_candle_low_price, last_candle_high_price, last_candle_low_price,
                   coin_abbreviation, threshold):
    # Check if the current price is within the threshold
    if min(last_candle_low_price, current_candle_low_price) <= threshold <= max(last_candle_high_price,
                                                                                current_candle_high_price):
        # TODO: Put call in queue
        pass
