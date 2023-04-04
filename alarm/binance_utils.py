import requests
import websocket
import json
import ssl


def get_binance_valid_list_of_symbols():
    BINANCE_API_URL = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(BINANCE_API_URL)

    if response.status_code == 200:
        valid_list_of_symbols = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
        return valid_list_of_symbols
    else:
        return []


def extract_binance_data_from_socket(coin_abbreviation, current_candle_high_price, threshold,
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
