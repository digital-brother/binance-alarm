from alarm.binance_utils import extract_binance_data_from_socket, parse_binance_data
from alarm.models import Candle, Coin


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

        last_candle_high_price = coin.last_high_price
        last_candle_low_price = coin.last_low_price

        extract_binance_data_from_socket(coin_abbreviation, current_candle_high_price, threshold,
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
