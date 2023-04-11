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


def any_of_key_pair_thresholds_is_broken(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
    penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

    if not last_candle or not penultimate_candle:
        logger.info(f"For {trade_pair} not enough candles data present "
                    f"(last candle {last_candle}, penultimate candle {penultimate_candle}).")
        return False

    for threshold in thresholds:
        threshold_broken = threshold_is_broken(threshold.price, last_candle, penultimate_candle)
        if threshold_broken:
            logger.info(f"For trade pair {trade_pair} threshold {threshold.price} was broken.")
            return True

    threshold_prices_str = ', '.join([str(threshold.price) for threshold in thresholds])
    logger.info(f"For {trade_pair} none of thresholds ({threshold_prices_str}) were broken.")
    return False
