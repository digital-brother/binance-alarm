import logging

from alarm.models import Threshold, Candle

logger = logging.getLogger(f'{__name__}')


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

    for threshold in thresholds:
        threshold_broken = threshold_is_broken(threshold.price, last_candle, penultimate_candle)
        logger.info(f"{str(trade_pair).upper()}; "
                    f"candles: {penultimate_candle}, {last_candle}; "
                    f"threshold: {threshold}; "
                    f"threshold broken: {threshold_broken}")
        if threshold_broken:
            return True

    return False
