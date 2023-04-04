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

