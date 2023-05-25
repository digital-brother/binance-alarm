import json
import logging
import ssl

import requests
import websocket

logger = logging.getLogger(f'{__name__}')


def get_binance_valid_trade_pairs():
    """Returns a dict in a format: {<trade_pair_name>' {'base_asset': , 'quote_asset': }}"""
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)
    if response.status_code != 200:
        raise requests.exceptions.RequestException("API request for get binance exchange data was failed")

    data = response.json()
    trade_pairs = data['symbols']
    binance_valid_trade_pairs = {}
    for trade_pair in trade_pairs:
        base_asset = trade_pair['baseAsset']
        quote_asset = trade_pair['quoteAsset']
        trade_pair_name = trade_pair['symbol']
        binance_valid_trade_pairs.update(
            {trade_pair_name: {
                'baseAsset': base_asset,
                'quoteAsset': quote_asset}
            }
        )
    return binance_valid_trade_pairs


def get_trade_pair_str(trade_pair):
    binance_valid_trade_pairs = get_binance_valid_trade_pairs()
    trade_pair_info = binance_valid_trade_pairs.get(trade_pair.upper())
    if trade_pair_info is None:
        raise ValueError(f"No matching trade pair found for '{trade_pair}'")

    base_asset = trade_pair_info['baseAsset']
    quote_asset = trade_pair_info['quoteAsset']
    return f"{base_asset}/{quote_asset}"


# TODO: function does almost the same as get_binance_valid_trade_pairs, refactor it
def get_binance_valid_trade_pairs_2():
    binance_valid_trade_pairs = get_binance_valid_trade_pairs()
    valid_list_of_trade_pairs = [trade_pair_name.lower() for trade_pair_name in binance_valid_trade_pairs]
    return valid_list_of_trade_pairs


def connect_binance_socket(trade_pairs):
    interval = '1s'
    websocket.enableTrace(False)
    trade_pairs_and_intervals_for_socket_url = '/'.join(
        [f'{trade_pair}@kline_{interval}' for trade_pair in trade_pairs])

    socket_url = f'wss://stream.binance.com:9443/ws/{trade_pairs_and_intervals_for_socket_url}'
    socket = websocket.create_connection(socket_url, sslopt={'cert_reqs': ssl.CERT_NONE})
    logger.info(f"Socket connected: {socket_url}.")

    return socket


def parse_candle_from_websocket_update(data):
    json_message = json.loads(data)
    candle = json_message['k']
    candle_high_price = float(candle['h'])
    candle_low_price = float(candle['l'])
    trade_pair = candle['s']
    trade_pair_lower_case = trade_pair.lower()

    return candle_high_price, candle_low_price, trade_pair_lower_case
