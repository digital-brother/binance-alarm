import json
import logging
import requests
import ssl
import websocket

logger = logging.getLogger(f'{__name__}')


def get_binance_valid_trade_pairs_with_base_quote_assets():
    binance_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(binance_exchange_info_url)
    if response.status_code != 200:
        raise requests.exceptions.RequestException("API request for get binance exchange data was failed")

    data = response.json()
    trade_pairs = data['symbols']
    trade_pairs_with_base_quote_assets = {}
    for trade_pair in trade_pairs:
        base_asset = trade_pair['baseAsset']
        quote_asset = trade_pair['quoteAsset']
        trade_pairs_with_base_quote_assets[trade_pair['symbol']] = {'baseAsset': base_asset, 'quoteAsset': quote_asset}
    return trade_pairs_with_base_quote_assets


def format_trade_pair_for_message(trade_pair):
    binance_valid_trade_pairs_with_base_quote_assets = get_binance_valid_trade_pairs_with_base_quote_assets()

    for trade_pair_with_base_quote_asset in binance_valid_trade_pairs_with_base_quote_assets:
        if trade_pair.upper() in trade_pair_with_base_quote_asset:
            base_asset = binance_valid_trade_pairs_with_base_quote_assets[trade_pair_with_base_quote_asset]['baseAsset']
            quote_asset = binance_valid_trade_pairs_with_base_quote_assets[trade_pair_with_base_quote_asset]['quoteAsset']
            trade_pair_str = f"{base_asset}/{quote_asset}"
            return trade_pair_str

    raise ValueError(f"No matching trade pair found for '{trade_pair}'")


def get_binance_valid_list_of_trade_pairs():
    binance_exchange_info = get_binance_valid_trade_pairs_with_base_quote_assets()

    valid_list_of_trade_pairs = [trade_pair_abbreviation.lower() for trade_pair_abbreviation in
                                 binance_exchange_info]
    return valid_list_of_trade_pairs


def close_binance_socket(socket):
    socket.close()


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
