import logging

from alarm.binance_utils import format_trade_pair_for_message

from twilio.rest import Client

from alarm.models import Threshold, Candle, ThresholdBrake, Phone
from binance_alarm.settings import ACCOUNT_SID, AUTH_TOKEN

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

logger = logging.getLogger(f'{__name__}')


def any_of_trade_pair_thresholds_is_broken(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
    penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

    if last_candle is None and penultimate_candle is None:
        return False

    for threshold in thresholds:
        threshold_broken = threshold.is_broken(last_candle, penultimate_candle)
        logger.info(f"{str(trade_pair).upper()}; "
                    f"candles: {penultimate_candle}, {last_candle}; "
                    f"threshold: {threshold}; "
                    f"threshold broken: {threshold_broken}")
        if threshold_broken:
            return True

    return False


def create_thresholds_brakes_from_recent_candles_update(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    for threshold in thresholds:
        ThresholdBrake.objects.create(threshold=threshold)


def get_thresholds_brake_prices(trade_pair):
    thresholds_brake_prices = ThresholdBrake.objects.filter(threshold__trade_pair=trade_pair).order_by(
        '-happened_at').values_list(
        'threshold__price', flat=True)
    return thresholds_brake_prices


def get_trade_pair_current_price(trade_pair):
    last_candle = Candle.last_for_trade_pair(trade_pair)
    return last_candle.high_price if last_candle else None


def create_message_for_threshold_break(trade_pair):
    trade_pair_str = format_trade_pair_for_message(trade_pair)

    thresholds_brake_prices = get_thresholds_brake_prices(trade_pair)

    thresholds_brake_prices_str = ', '.join([f'{price}$' for price in thresholds_brake_prices])

    trade_pair_current_price = get_trade_pair_current_price(trade_pair)

    message = f"Attention! Trade pair {trade_pair_str} has broken thresholds {thresholds_brake_prices_str} and " \
              f"the current price is {trade_pair_current_price}$"

    return message


def create_twiml_response_for_threshold_break(trade_pair):
    message = create_message_for_threshold_break(trade_pair)
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def refresh_message_about_threshold_break(trade_pair):
    message = create_message_for_threshold_break(trade_pair)
    phones = Phone.objects.filter(threshold__trade_pair=trade_pair)

    if not phones:
        logger.error('Phones are not found for the trade pair')
        return

    for phone in phones:
        phone.refresh_message(message)


def make_call():
    print('MAKE CALL')
