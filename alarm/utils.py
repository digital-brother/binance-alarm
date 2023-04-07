from alarm.binance_utils import parse_binance_data, print_binance_candle_data
from alarm.models import Coin


def update_coin_candle_from_binance_data(data):
    try:
        # Parse the message to extract relevant data
        current_candle_high_price, current_candle_low_price, abbreviation = parse_binance_data(data)

        coin = Coin.objects.filter(abbreviation=abbreviation).first()

        if not coin:
            # There is no coin with this abbreviation in the database
            # TODO: Show error with Sentry
            return

        coin.update_or_create_candles(current_candle_high_price, current_candle_low_price)

        threshold = coin.threshold

        last_candle_high_price = coin.last_high_price
        last_candle_low_price = coin.last_low_price

        print_binance_candle_data(abbreviation, current_candle_high_price, threshold,
                                  current_candle_low_price)
        coin_prices_data = {
            'current_candle_high_price': current_candle_high_price,
            'current_candle_low_price': current_candle_low_price,
            'threshold': threshold,
            'last_candle_high_price': last_candle_high_price,
            'last_candle_low_price': last_candle_low_price
        }

        return coin_prices_data

    except (KeyError, ValueError, TypeError) as e:
        # An error occurred while parsing the message
        # TODO: Show error with Sentry
        pass


def if_threshold_breaks(coin_prices_data):
    if coin_prices_data:
        threshold = coin_prices_data['threshold']
        last_candle_high_price = coin_prices_data['last_candle_high_price']
        current_candle_high_price = coin_prices_data['current_candle_high_price']
        last_candle_low_price = coin_prices_data['last_candle_low_price']
        current_candle_low_price = coin_prices_data['current_candle_low_price']

        return min(last_candle_low_price, current_candle_low_price) <= threshold <= max(last_candle_high_price,
                                                                                        current_candle_high_price)
