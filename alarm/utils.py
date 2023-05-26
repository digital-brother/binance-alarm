import logging

from alarm.binance_utils import get_trade_pair_str

from twilio.rest import Client

from alarm.models import Threshold, Candle, ThresholdBrake, Phone
from binance_alarm.settings import ACCOUNT_SID, AUTH_TOKEN

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

logger = logging.getLogger(f'{__name__}')


def create_thresholds_brakes_from_recent_candles_update(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
    penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

    if last_candle is None or penultimate_candle is None:
        return []

    threshold_brakes = []
    for threshold in thresholds:
        threshold_broken = threshold.is_broken(last_candle, penultimate_candle)
        logger.info(f"{str(trade_pair).upper()}; "
                    f"candles: {penultimate_candle}, {last_candle}; "
                    f"threshold: {threshold}; "
                    f"threshold broken: {threshold_broken}")
        if threshold_broken:
            threshold_brake = ThresholdBrake.objects.create(threshold=threshold)
            threshold_brakes.append(threshold_brake)

    return threshold_brakes


def get_trade_pair_thresholds_brakes_prices(trade_pair):
    thresholds_brake_prices = ThresholdBrake.objects.filter(threshold__trade_pair=trade_pair).order_by(
        '-happened_at').values_list(
        'threshold__price', flat=True)
    return thresholds_brake_prices


# TODO: Refactor to use closing price
def get_trade_pair_current_price(trade_pair):
    last_candle = Candle.last_for_trade_pair(trade_pair)
    return last_candle.high_price if last_candle else None


def get_trade_pair_alarm_message(trade_pair):
    trade_pair_str = get_trade_pair_str(trade_pair)

    thresholds_brakes_prices = get_trade_pair_thresholds_brakes_prices(trade_pair)
    thresholds_brake_prices_str = ', '.join([f'{price}$' for price in thresholds_brakes_prices])

    trade_pair_current_price = get_trade_pair_current_price(trade_pair)

    return f"{trade_pair_str} broken thresholds {thresholds_brake_prices_str}; " \
           f"the current {trade_pair_str} price is {trade_pair_current_price}$."


def get_message_with_twiml_elements_for_threshold_break(trade_pair):
    message = get_trade_pair_alarm_message(trade_pair)
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def refresh_phone_alarm_message():
    threshold_brakes = ThresholdBrake.objects.all()
    trade_pairs = threshold_brakes.values_list('threshold__trade_pair', flat=True).distinct()
    thresholds = threshold_brakes.values_list('threshold__price', flat=True)

    for trade_pair in trade_pairs:
        message = get_trade_pair_alarm_message(trade_pair)
        for threshold in thresholds:
            broken_thresholds = Threshold.objects.filter(trade_pair=trade_pair, price=threshold)

            for broken_threshold in broken_thresholds:
                phone = broken_threshold.phone
                phone.refresh_message(message)


def make_call():
    print('MAKE CALL')
