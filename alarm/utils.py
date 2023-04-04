from alarm.models import Coin, Candle
import websocket
import json
import ssl


def extract_data_from_socket(coin_abbreviation, current_candle_high_price, threshold,
                             current_candle_low_price):
    print(
        f"Coin Abbreviation: {coin_abbreviation}, High Price: {current_candle_high_price}, Threshold: {threshold}, "
        f"Low Price: {current_candle_low_price}")


def close_binance_sockets(sockets):
    for i, socket in enumerate(sockets):
        socket.close()


def connect_binance_socket(currencies):
    INTERVAL = '1s'
    websocket.enableTrace(False)
    socket_urls = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{INTERVAL}' for currency in
                   currencies]

    sockets = []
    for socket_url in socket_urls:
        socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
        sockets.append(socket)

    return sockets


def parse_binance_data(data):
    json_message = json.loads(data)
    current_candle = json_message['k']
    current_candle_high_price = float(current_candle['h'])
    current_candle_low_price = float(current_candle['l'])
    coin_symbol = current_candle['s']
    coin_abbreviation = coin_symbol.lower()

    return current_candle_high_price, current_candle_low_price, coin_abbreviation


def get_binance_data_and_update_coin_candle(data):
    try:
        # Parse the message to extract relevant data
        current_candle_high_price, current_candle_low_price, coin_abbreviation = parse_binance_data(data)

        coin = Coin.objects.filter(coin_abbreviation=coin_abbreviation).first()

        if not coin:
            # There is no coin with this abbreviation in the database
            # TODO: Handle this case appropriately
            return

        coin.update_or_create_candles(current_candle_high_price, current_candle_low_price)

        threshold = coin.threshold
        coin_property = Candle.objects.filter(coin=coin).last()

        if not coin_property:
            # There are no candles for this coin yet
            # TODO: Handle this case appropriately
            return

        last_candle_high_price = coin_property.last_high_price
        last_candle_low_price = coin_property.last_low_price

        extract_data_from_socket(coin_abbreviation, current_candle_high_price, threshold,
                                 current_candle_low_price)
        prices = {
            'current_candle_high_price': current_candle_high_price,
            'current_candle_low_price': current_candle_low_price,
            'threshold': threshold,
            'last_candle_high_price': last_candle_high_price,
            'last_candle_low_price': last_candle_low_price
        }

        return prices

    except (KeyError, ValueError, TypeError) as e:
        # An error occurred while parsing the message
        # TODO: Handle this case appropriately
        pass


def check_if_call_needed(prices):

    threshold = prices['threshold']
    last_candle_high_price = prices['last_candle_high_price']
    current_candle_high_price = prices['current_candle_high_price']
    last_candle_low_price = prices['last_candle_low_price']
    current_candle_low_price = prices['current_candle_low_price']
    if min(last_candle_low_price, current_candle_low_price) <= threshold <= max(last_candle_high_price,
                                                                                current_candle_high_price):
        result = True
    else:
        result = False

    return result
