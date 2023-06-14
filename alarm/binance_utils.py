import json
import logging
import ssl

import requests
import websocket

logger = logging.getLogger(f'{__name__}')


def get_binance_valid_trade_pairs():
    """
    Needed to get Binance valid trade pairs data, convert to a handy for a usage format.
    Returns a dict in a format: {trade_pair_name': {'base_asset': 'str', 'quote_asset': 'str'}}.
    """
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)
    if response.status_code != 200:
        raise requests.exceptions.RequestException("Get Binance valid trade pairs request failed.")

    data = response.json()
    trade_pairs = data['symbols']
    binance_valid_trade_pairs = {}
    for trade_pair in trade_pairs:
        base_asset = trade_pair['baseAsset']
        quote_asset = trade_pair['quoteAsset']
        trade_pair_name = trade_pair['symbol']
        # TODO: remove trade pair lower
        binance_valid_trade_pairs.update(
            {trade_pair_name.lower(): {
                'baseAsset': base_asset,
                'quoteAsset': quote_asset}
            }
        )
    return binance_valid_trade_pairs


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
    candle_close_price = float(candle['c'])
    trade_pair = candle['s']
    # TODO: remove trade pair lower
    trade_pair_lower_case = trade_pair.lower()
    return candle_high_price, candle_low_price, candle_close_price, trade_pair_lower_case
