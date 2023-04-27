import logging
import time
from alarm.binance_utils import format_trade_pair_for_message

from twilio.rest import Client

from alarm.models import Threshold, Candle, ThresholdBrake
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
            # create_threshold_brake(trade_pair)
            return True

    return False


def create_threshold_brake(trade_pair):
    thresholds = Threshold.objects.filter(trade_pair=trade_pair)
    message = create_message_about_threshold_break(trade_pair)
    for threshold in Threshold.objects.filter(trade_pair=trade_pair):
        if ThresholdBrake.objects.filter(threshold=threshold).exists():
            continue
    for threshold in thresholds:
        try:
            latest_threshold_brake = ThresholdBrake.objects.filter(message=message).latest('happened_at')
            if latest_threshold_brake:
                return False
        except ThresholdBrake.DoesNotExist:
            pass

        ThresholdBrake.objects.create(threshold=threshold, message=message)


def create_message_about_threshold_break(trade_pair):
    threshold_prices = Threshold.objects.filter(trade_pair=trade_pair).values_list('price', flat=True)

    threshold_prices_str = ', '.join([f'{price}$' for price in threshold_prices])
    trade_pair_str = format_trade_pair_for_message(trade_pair)

    last_candle = Candle.objects.filter(trade_pair=trade_pair).order_by('-modified').last()

    last_candle_high_price = last_candle.high_price if last_candle else None
    message = f"<Response><Say>Attention! Trade pair {trade_pair_str} has broken thresholds {threshold_prices_str} and current price is {last_candle_high_price}$</Say></Response>"
    return message


def make_call():
    print("CALL USER")


def handle_call_status(call, message):
    while True:
        call = call.fetch()
        if call.status == 'completed':
            # TODO: Delete old info about threshold break
            time.sleep(900)
            break
        elif call.status == 'canceled':
            call = twilio_client.calls.create(
                twiml=message,
                to=USER_PHONE_NUMBER,
                from_=PHONE_NUMBER_TWILLIO
            )
        elif call.status in ['ringing', 'answered', 'in-progress']:
            time.sleep(60)
            call = call.fetch()
            if call.status == 'completed':
                # TODO: Delete old info about threshold break
                break
            elif call.status == 'no-answer':
                for i in range(15):
                    time.sleep(60)
                    call = twilio_client.calls.create(
                        twiml=message,
                        to=USER_PHONE_NUMBER,
                        from_=PHONE_NUMBER_TWILLIO
                    )
                    call = call.fetch()
                    if call.status in ['ringing', 'answered', 'in-progress']:
                        time.sleep(60)
                        call = call.fetch()
                        if call.status == 'completed':
                            # TODO: Delete old info about threshold break
                            break
            else:
                break
        elif call.status in ['queued', 'busy', 'failed']:
            time.sleep(60)
            call = twilio_client.calls.create(
                twiml=message,
                to=USER_PHONE_NUMBER,
                from_=PHONE_NUMBER_TWILLIO
            )
        else:
            break
