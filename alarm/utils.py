import logging

from alarm.binance_utils import get_trade_pair_str

from alarm.models import Threshold, Candle, ThresholdBrake, Phone, TradePair

logger = logging.getLogger(f'{__name__}')


def get_trade_pair_alarm_message(number, trade_pair):
    trade_pair_str = get_trade_pair_str(trade_pair)

    # TODO:
    threshold_brakes_prices_str = TradePair(number, trade_pair).thresholds_brakes_prices_str
    trade_pair_close_price = Candle.get_trade_pair_close_price(trade_pair)

    message = f"{trade_pair_str} broken thresholds {threshold_brakes_prices_str} and the current {trade_pair_str} price is {trade_pair_close_price}$."

    return message


def get_message_with_twiml_elements_for_threshold_break(trade_pair):
    message = get_trade_pair_alarm_message(trade_pair, )
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def make_call():
    print('MAKE CALL')
