import logging

from alarm.models import TradePair

logger = logging.getLogger(f'{__name__}')


def get_message_with_twiml_elements_for_threshold_break(phone, trade_pair):
    message = TradePair(phone, trade_pair).get_trade_pair_alarm_message()
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def make_call():
    print('MAKE CALL')
