import logging

from alarm.models import Threshold, Candle, ThresholdBrake

import time
from twilio.rest import Client

from binance_alarm.settings import ACCOUNT_SID, AUTH_TOKEN, PHONE_NUMBER_TWILLIO, USER_PHONE_NUMBER

client = Client(ACCOUNT_SID, AUTH_TOKEN)

logger = logging.getLogger(f'{__name__}')


def threshold_is_broken(threshold_price, previous_candle, current_candle):
    if previous_candle:
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


def check_call_status(call, message):
    if call.status == 'completed':
        # Sleep for 15 minutes
        time.sleep(900)
    elif call.status == 'busy' or call.status == 'failed':
        # Sleep for 1 minute and create a new call
        time.sleep(60)
        call = client.calls.create(
            twiml=message,
            to=USER_PHONE_NUMBER,
            from_=PHONE_NUMBER_TWILLIO
        )
        check_call_status(call)
    else:
        # Try to call the user every minute for 15 minutes
        for i in range(15):
            time.sleep(60)
            call = client.calls.create(
                twiml=message,
                to=USER_PHONE_NUMBER,
                from_=PHONE_NUMBER_TWILLIO
            )
            if call.status == 'completed':
                break
            elif i == 14:
                # Maximum attempts reached, exit the loop
                break
