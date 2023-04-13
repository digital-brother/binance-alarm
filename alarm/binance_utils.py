import json
import logging
import requests
import ssl
import websocket

logger = logging.getLogger(f'{__name__}')


def get_binance_trade_pairs():
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)

    if response.status_code == 200:
        valid_list_of_coin_names = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
        return valid_list_of_coin_names
    else:
        return []


def close_binance_socket(socket):
    socket.close()


def connect_binance_socket(trade_pairs):
    interval = '1s'
    websocket.enableTrace(False)
    trade_pairs_and_intervals_for_socket_url = '/'.join(
        [f'{trade_pair}@kline_{interval}' for trade_pair in trade_pairs])

    socket_url = f'wss://stream.binance.com:9443/ws/{trade_pairs_and_intervals_for_socket_url}'
    socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
    logger.info(f"Sockets connected: {socket_url}.")

    return socket


def parse_candle_from_websocket_update(data):
    json_message = json.loads(data)
    candle = json_message['k']
    candle_high_price = float(candle['h'])
    candle_low_price = float(candle['l'])
    trade_pair = candle['s']
    trade_pair_lower_case = trade_pair.lower()

    return candle_high_price, candle_low_price, trade_pair_lower_case
