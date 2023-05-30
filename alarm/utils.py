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


# def get_trade_pair_thresholds_brakes_prices(trade_pair):
#     phones = Phone.get_numbers_with_trade_pair(trade_pair=trade_pair)
#
#     for phone in phones:
#         thresholds = Threshold.objects.filter(phone=phone)
#
#         threshold_brake_prices = ThresholdBrake.objects.filter(threshold__in=thresholds,
#                                                                threshold__trade_pair=trade_pair).values_list(
#             'threshold__price', flat=True)
#         return threshold_brake_prices

# def get_trade_pair_thresholds_brakes_prices_str(phone, trade_pair):
#     thresholds = Threshold.objects.filter(phone=phone, trade_pair=trade_pair)
#     threshold_brake_prices = ThresholdBrake.objects.filter(threshold__in=thresholds).order_by(
#         '-happened_at').values_list('threshold__price',
#                                     flat=True)
#     thresholds_brake_prices_str = ", ".join([f'{price}$' for price in threshold_brake_prices])
#     return thresholds_brake_prices_str


def get_trade_pair_thresholds_brakes_prices_with_number(trade_pair):
    phone_numbers = Phone.objects.values_list('number', flat=True)
    thresholds = Threshold.objects.filter(phone__number__in=phone_numbers, trade_pair=trade_pair)
    threshold_brake_prices = ThresholdBrake.objects.filter(threshold__in=thresholds).order_by(
        '-happened_at').values_list('threshold__phone__number', 'threshold__price', 'threshold__trade_pair')

    return threshold_brake_prices


# TODO: Refactor to use closing price
def get_trade_pair_current_price(trade_pair):
    last_candle = Candle.last_for_trade_pair(trade_pair)
    return last_candle.high_price if last_candle else None


def converted_trade_pair_thresholds_brakes_prices_with_number(trade_pair):
    threshold_brake_prices_by_numbers = get_trade_pair_thresholds_brakes_prices_with_number(trade_pair)
    dict_with_threshold_brake_prices_by_number = {}
    for threshold_brake_price_by_numbers in threshold_brake_prices_by_numbers:
        number, threshold, trade_pair = threshold_brake_price_by_numbers
        if number in dict_with_threshold_brake_prices_by_number:
            dict_with_threshold_brake_prices_by_number[number]['thresholds'].add(threshold)
        else:
            dict_with_threshold_brake_prices_by_number[number] = {'number': number, 'trade_pair': trade_pair,
                                                                  'thresholds': {threshold}}

    # Convert sets to lists for easier serialization (optional)
    for entry in dict_with_threshold_brake_prices_by_number.values():
        entry['thresholds'] = list(entry['thresholds'])
    return dict_with_threshold_brake_prices_by_number


def get_trade_pair_alarm_message(number, trade_pair):
    #     trade_pair_str = get_trade_pair_str(trade_pair)
    #
    #     thresholds_brakes_prices = get_trade_pair_thresholds_brakes_prices(trade_pair)
    #     thresholds_brake_prices_str = ', '.join([f'{price}$' for price in thresholds_brakes_prices])
    #
    #     trade_pair_current_price = get_trade_pair_current_price(trade_pair)
    #
    #     return f"{trade_pair_str} broken thresholds {thresholds_brake_prices_str}; " \
    #            f"the current {trade_pair_str} price is {trade_pair_current_price}$."

    phones = Phone.objects.all()
    converted_trade_pair_thresholds_brakes_prices_with_numbers = converted_trade_pair_thresholds_brakes_prices_with_number(
        trade_pair)

    for phone in phones:
        trade_pair_str = get_trade_pair_str(trade_pair)
        trade_pair_current_price = get_trade_pair_current_price(trade_pair)

        return f"{trade_pair_str} broken thresholds {converted_trade_pair_thresholds_brakes_prices_with_number}; " \
               f"the current {trade_pair_str} price is {trade_pair_current_price}$."


# def get_message_with_twiml_elements_for_threshold_break(trade_pair):
#     message = get_trade_pair_alarm_message(trade_pair)
#     message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
#     return message_with_twiml_elements


def refresh_phone_alarm_message():
    phones = Phone.objects.all()
    threshold_brakes = ThresholdBrake.objects.all()
    for threshold_brake in threshold_brakes:
        trade_pair = threshold_brake.threshold.trade_pair
        message = get_trade_pair_alarm_message(trade_pair)
    for phone in phones:
        phone.refresh_message(message)


def make_call():
    print('MAKE CALL')
