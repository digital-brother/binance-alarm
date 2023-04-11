import requests
import websocket
import json
import ssl


def get_binance_trade_pairs():
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)

    if response.status_code == 200:
        valid_list_of_coin_names = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
        return valid_list_of_coin_names
    else:
        return []


def close_binance_sockets(sockets):
    for i, socket in enumerate(sockets):
        socket.close()


def connect_binance_sockets(trade_pairs):
    interval = '1s'
    websocket.enableTrace(False)
    socket_urls = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency in trade_pairs]
    sockets = []
    for socket_url in socket_urls:
        socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
        sockets.append(socket)

    print(f"Sockets connected: {', '.join(socket_urls)}.")
    return sockets


def parse_kindle_data(data):
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
