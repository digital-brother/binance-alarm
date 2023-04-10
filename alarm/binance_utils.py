import requests
import websocket
import json
import ssl


def get_binance_list_of_trade_pairs():
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)

    if response.status_code == 200:
        valid_list_of_coin_names = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
        return valid_list_of_coin_names
    else:
        return []


def print_binance_candle_data(abbreviation, current_candle_high_price, threshold,
                              current_candle_low_price):
    print(
        f"Coin Abbreviation: {abbreviation}, High Price: {current_candle_high_price}, Threshold: {threshold}, "
        f"Low Price: {current_candle_low_price}")


def close_binance_sockets(sockets):
    for i, socket in enumerate(sockets):
        socket.close()


def connect_binance_sockets(currencies):
    interval = '1s'
    websocket.enableTrace(False)
    socket_urls = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency in
                   currencies]
    sockets = []
    for socket_url in socket_urls:
        socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
        sockets.append(socket)

    return sockets


def parse_kindle_data_from_binance_websocket_update(data):
    """
        Parses the data received from Binance WebSocket API and returns the high price,
        low price, and trade_pair of the coin for the current candle.
    """
    json_message = json.loads(data)
    candle = json_message['k']
    candle_high_price = float(candle['h'])
    candle_low_price = float(candle['l'])
    trade_pair = candle['s']
    trade_pair_lower_case = trade_pair.lower()

    return candle_high_price, candle_low_price, trade_pair_lower_case
