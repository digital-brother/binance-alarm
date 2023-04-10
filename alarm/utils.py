from alarm.binance_utils import parse_kindle_data_from_binance_websocket_update, print_binance_candle_data
from alarm.models import Threshold


def update_coin_candle_from_binance_data(data):
    try:
        # Parse the message to extract relevant data
        current_candle_high_price, current_candle_low_price, trade_pair = \
            parse_kindle_data_from_binance_websocket_update(data)

        threshold = Threshold.objects.filter(abbreviation=trade_pair).first()

        if not threshold:
            # There is no coin with this trade_pair in the database
            # TODO: Show error with Sentry
            return

        threshold.update_or_create_candles(current_candle_high_price, current_candle_low_price)

        threshold = threshold.price

        last_candle_high_price = threshold.last_high_price
        last_candle_low_price = threshold.last_low_price

        print_binance_candle_data(trade_pair, current_candle_high_price, threshold,
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


def threshold_is_broken(coin_prices_data):
    if coin_prices_data:
        threshold = coin_prices_data['threshold']
        last_candle_high_price = coin_prices_data['last_candle_high_price']
        current_candle_high_price = coin_prices_data['current_candle_high_price']
        last_candle_low_price = coin_prices_data['last_candle_low_price']
        current_candle_low_price = coin_prices_data['current_candle_low_price']

        return min(last_candle_low_price, current_candle_low_price) <= threshold <= max(last_candle_high_price,
                                                                                        current_candle_high_price)
