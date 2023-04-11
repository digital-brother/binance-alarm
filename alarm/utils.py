import logging

from alarm.models import Threshold, Candle

logger = logging.getLogger(f'django.{__name__}')


def threshold_is_broken(threshold_price, previous_candle, current_candle):
    if previous_candle:
        return (
                min(previous_candle.low_price, current_candle.low_price) <=
                threshold_price <=
                max(previous_candle.high_price, current_candle.high_price)
        )
    return False


def any_of_key_pair_thresholds_is_broken(trade_pair, current_candle):
    previous_candle = Candle.objects.get(trade_pair=trade_pair)
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)

    for threshold in thresholds:
        threshold_broken = threshold_is_broken(threshold.price, previous_candle, current_candle)
        if threshold_broken:
            return True

    threshold_prices_str = ', '.join([str(threshold.price) for threshold in thresholds])
    logger.info(f"For {trade_pair} none of thresholds ({threshold_prices_str}) were broken")
    return False