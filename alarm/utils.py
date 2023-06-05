import logging

from alarm.binance_utils import get_trade_pair_str

from alarm.models import Threshold, Candle, ThresholdBrake, Phone

logger = logging.getLogger(f'{__name__}')


def create_thresholds_brakes_from_recent_candles_update(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
    penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)
    trade_pair_close_price = Candle.get_trade_pair_close_price(trade_pair)

    if last_candle is None or penultimate_candle is None:
        return []

    threshold_brakes = []
    for threshold in thresholds:
        threshold_broken = threshold.is_broken(last_candle, penultimate_candle)
        logger.info(f"{str(trade_pair).upper()}; "
                    f"candles: {penultimate_candle}, {last_candle}, {trade_pair_close_price}; "
                    f"threshold: {threshold}; "
                    f"threshold broken: {threshold_broken};")
        if threshold_broken:
            threshold_brake = ThresholdBrake.objects.get_or_create(threshold=threshold)
            threshold_brakes.append(threshold_brake)

    return threshold_brakes


def get_trade_pair_thresholds_brakes_prices_str(number, trade_pair):
    phone = Phone.objects.get(number=number)
    thresholds = phone.thresholds.filter(trade_pair=trade_pair)
    threshold_brake_prices = ThresholdBrake.objects.filter(threshold__in=thresholds).order_by(
        '-happened_at').values_list('threshold__price', flat=True)
    thresholds_brake_prices_str = ', '.join([f'{price}$' for price in threshold_brake_prices])
    return thresholds_brake_prices_str


def get_alarm_message(number, trade_pair):
    trade_pair_str = get_trade_pair_str(trade_pair)

    threshold_brake_prices_str = get_trade_pair_thresholds_brakes_prices_str(number, trade_pair)
    trade_pair_close_price = Candle.get_trade_pair_close_price(trade_pair)

    message = f"{trade_pair_str} broken thresholds {threshold_brake_prices_str} and the current {trade_pair_str} price is {trade_pair_close_price}$."

    return message


def get_message_with_twiml_elements_for_threshold_break(trade_pair):
    message = get_alarm_message(trade_pair)
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def make_call():
    print('MAKE CALL')
