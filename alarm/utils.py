import logging
from datetime import timedelta

from django.utils import timezone

from alarm.binance_utils import format_trade_pair_for_message

from twilio.rest import Client

from alarm.models import Threshold, Candle, ThresholdBrake, Phone
from binance_alarm.settings import ACCOUNT_SID, AUTH_TOKEN, PHONE_NUMBER_TWILLIO, USER_PHONE_NUMBER

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


def create_message_for_threshold_break(trade_pair):
    three_second_ago = timezone.now() - timedelta(seconds=3)

    messages = {}

    trade_pair_str = format_trade_pair_for_message(trade_pair)

    threshold_brake_prices = list(
        ThresholdBrake.objects.filter(threshold__trade_pair=trade_pair, happened_at__gte=three_second_ago).values_list(
            'threshold__price', flat=True))

    threshold_brake_prices_str = ', '.join([f'{price}$' for price in threshold_brake_prices])

    last_candle = Candle.objects.filter(trade_pair=trade_pair).order_by('-modified').last()
    last_candle_high_price = last_candle.high_price if last_candle else None

    message = messages.setdefault(trade_pair,
                                  f" Attention! Trade pair {trade_pair_str} has broken thresholds ")
    message += f'{threshold_brake_prices_str} and current price is {last_candle_high_price}$ '
    messages[trade_pair] = message
    return ''.join(messages.values())


def combine_threshold_break_messages(trade_pair):
    messages = create_message_for_threshold_break(trade_pair)
    message_with_twiml_elements = '<Response><Say>'
    message_with_twiml_elements += ''.join(messages)
    message_with_twiml_elements += '</Say></Response>'
    return message_with_twiml_elements


def refresh_message_about_threshold_break(trade_pair):
    message = combine_threshold_break_messages(trade_pair)
    threshold = Threshold.objects.filter(trade_pair=trade_pair).first()

    if not threshold:
        logger.error('Threshold is not found')
        return

    threshold.phone.refresh_message(message)


def make_call():
    print('MAKE CALL')
