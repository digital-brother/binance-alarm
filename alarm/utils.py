import logging

from alarm.binance_utils import formatting_trade_pair_for_user_message, connect_binance_socket
from alarm.models import Threshold, Candle, ThresholdBrake

from twilio.rest import Client

from binance_alarm.settings import ACCOUNT_SID, AUTH_TOKEN, PHONE_NUMBER_TWILLIO, USER_PHONE_NUMBER

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

logger = logging.getLogger(f'{__name__}')


def threshold_is_broken(threshold_price, previous_candle, current_candle):
    if previous_candle and current_candle:
        return (
                min(previous_candle.low_price, current_candle.low_price) <=
                threshold_price <=
                max(previous_candle.high_price, current_candle.high_price)
        )
    return False


def any_of_trade_pair_thresholds_is_broken(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
    penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

    if last_candle is None and penultimate_candle is None:
        return False

    for threshold in thresholds:
        threshold_broken = threshold_is_broken(threshold.price, last_candle, penultimate_candle)
        logger.info(f"{str(trade_pair).upper()}; "
                    f"candles: {penultimate_candle}, {last_candle}; "
                    f"threshold: {threshold}; "
                    f"threshold broken: {threshold_broken}")
        if threshold_broken:
            ThresholdBrake.objects.create(threshold=threshold)
            return True

    return False


def make_call(trade_pair):
    threshold_prices = Threshold.objects.filter(trade_pair=trade_pair).values_list('price', flat=True)

    formatted_prices_for_user_message = ', '.join([f'{price}$' for price in threshold_prices])
    formatted_trade_pair_for_user_message = formatting_trade_pair_for_user_message(trade_pair)

    last_candle = Candle.objects.filter(trade_pair=trade_pair).order_by('-modified').last()

    last_candle_high_price = last_candle.high_price if last_candle else None
    message = f"<Response><Say>Attention! Trade pair {formatted_trade_pair_for_user_message} has broken thresholds {formatted_prices_for_user_message} and current price is {last_candle_high_price}$</Say></Response>"
    call = twilio_client.calls.create(
        twiml=message,
        to=USER_PHONE_NUMBER,
        from_=PHONE_NUMBER_TWILLIO
    )

    # TODO: processing_call_status(call, message)
