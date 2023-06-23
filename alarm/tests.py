from unittest.mock import patch, Mock

import decimal

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from pytest_factoryboy import register

from alarm.factories import ThresholdFactory, CandleFactory, ThresholdBrakeFactory, PhoneFactory, UserFactory
from alarm.models import TradePair, ThresholdBrake, CallStatus

pytestmark = pytest.mark.django_db

register(UserFactory)
register(PhoneFactory)
register(ThresholdFactory)
register(ThresholdBrakeFactory)
register(CandleFactory)


class TestThresholdIsBroken:
    def test__threshold_is_broken__single_candle(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        candle = CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'))
        assert threshold.is_broken(None, candle)

    def test__threshold_not_broken__single_candle(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
        assert not threshold.is_broken(None, candle)

    def test__threshold_is_broken__two_candles(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('9.00'))
        second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('11.00'))
        assert threshold.is_broken(first_candle, second_candle)

    def test__threshold_not_broken__two_candles(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
        second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
        assert not threshold.is_broken(first_candle, second_candle)

    def test__threshold_is_broken__two_candles_with_gap(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
        second_candle = CandleFactory(low_price=Decimal('12.00'), high_price=Decimal('13.00'))
        assert threshold.is_broken(first_candle, second_candle)


class TestCreateThresholdBrake:
    def test__create_threshold_brake__threshold_broken(self):
        trade_pair = 'LUNAUSDT'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 1
        assert ThresholdBrake.objects.first().threshold == threshold


    def test__create_threshold_brake__does_not_create_duplicate(self):
        trade_pair = 'LUNAUSDT'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 1

    def test__create_threshold_brake__does_not_create_duplicate_for_two_thresholds(self, threshold):
        trade_pair = 'LUNAUSDT'
        ThresholdFactory(price=Decimal('12.00'), trade_pair=threshold.trade_pair, phone=threshold.phone)
        CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('14.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 2

    def test__create_threshold_brake__threshold_not_broken(self):
        trade_pair = 'LUNAUSDT'
        ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 0


class TestTradePairAlarmMessage:
    def test__trade_pair_alarm_message__no_threshold_brakes(self, phone):
        trade_pair_obj = TradePair(phone=phone, trade_pair='LUNAUSDT')
        assert trade_pair_obj.alarm_message is None

    def test__trade_pair_alarm_message__single_threshold_brake(self):
        threshold_brake = ThresholdBrakeFactory()
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_brake.threshold.phone, trade_pair=threshold_brake.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__trade_pair_alarm_message__another_trade_pair_threshold_brake_not_shown(self, threshold_brake):
        wing_threshold = ThresholdFactory(trade_pair='wingusdt', phone=threshold_brake.threshold.phone)
        ThresholdBrakeFactory(threshold=wing_threshold)
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_brake.threshold.phone, trade_pair=threshold_brake.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__trade_pair_alarm_message__three_threshold_brakes(self):
        first_threshold = ThresholdFactory()
        second_threshold = ThresholdFactory(phone=first_threshold.phone, price=decimal.Decimal('12.00'))

        first_threshold_brake = ThresholdBrakeFactory(threshold=first_threshold)
        ThresholdBrakeFactory(threshold=second_threshold)
        ThresholdBrakeFactory(threshold=first_threshold)

        CandleFactory()

        trade_pair_obj = TradePair(
            phone=first_threshold_brake.threshold.phone, trade_pair=first_threshold_brake.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00, 12.00, 10.00 and the current LUNA price is 14.00.'


class TestPhoneAlarmMessage:
    def test__phone_alarm_message__no_brakes(self, phone):
        assert phone.alarm_message is None

    def test__phone_alarm_message__single_trade_pair_broken(self, threshold_brake, candle):
        assert threshold_brake.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__phone_alarm_message__two_trade_pairs_broken(self, threshold_brake, candle):
        threshold_two = ThresholdFactory(trade_pair='WINGUSDT', price='20.00', phone=threshold_brake.threshold.phone)
        CandleFactory(trade_pair='WINGUSDT', close_price=decimal.Decimal('24.00'))
        ThresholdBrakeFactory(threshold=threshold_two)
        assert threshold_brake.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.\n' \
               'WING broken thresholds 20.00 and the current WING price is 24.00.'

    def test__phone_alarm_message__another_phone_trade_pair_broken(self, threshold_brake, candle):
        ThresholdBrakeFactory()
        assert threshold_brake.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'


def test__create_threshold_brakes_and_get_alarm_message():
    second_trade_pair = 'WINGUSDT'
    threshold = ThresholdFactory(price=decimal.Decimal(10.00))
    # Second trade pair threshold
    ThresholdFactory(price=decimal.Decimal(12.00), trade_pair=threshold.trade_pair, phone=threshold.phone)
    # Second trade pair threshold
    ThresholdFactory(trade_pair=second_trade_pair, price=decimal.Decimal(25.00), phone=threshold.phone)
    # Another phone threshold
    ThresholdFactory(price=decimal.Decimal(14.00), trade_pair=threshold.trade_pair)

    CandleFactory(low_price=decimal.Decimal(8.00), high_price=decimal.Decimal(16.00))
    CandleFactory(trade_pair=second_trade_pair, low_price=decimal.Decimal(21.00), high_price=decimal.Decimal(29.00))
    TradePair.create_thresholds_brakes_from_recent_candles_update(threshold.trade_pair)
    TradePair.create_thresholds_brakes_from_recent_candles_update(second_trade_pair)
    assert ThresholdBrake.objects.count() == 4
    assert threshold.phone.alarm_message == \
           'LUNA broken thresholds 10.00, 12.00 and the current LUNA price is 12.00.\n' \
           'WING broken thresholds 25.00 and the current WING price is 25.00.'


class TestPhoneCall:
    @pytest.mark.xfail(ValidationError)
    def test__call__no_alarm_message(self, phone):
        phone.call()

    @pytest.mark.xfail(ValidationError)
    @patch('alarm.models.twilio_utils.call', Mock(return_value='twilio_sid'))
    def test__call__alarm_message_not_synced(self, threshold_brake):
        phone = threshold_brake.threshold.phone
        phone.call()
        phone.call()

    @pytest.mark.xfail(ValidationError)
    def test__handle_user_notified_if_call_succeed__no_previous_call(self, phone):
        phone.handle_user_notified_if_call_succeed()

    @patch('alarm.models.twilio_utils.call', Mock(return_value='twilio_sid'))
    @patch('alarm.models.twilio_utils.call_status', Mock(return_value=CallStatus.SUCCEED))
    @patch('alarm.models.telegram_utils.send_message', Mock())
    @patch('alarm.models.twilio_utils.cancel_call', Mock())
    def test__handle_user_notified_if_call_succeed__after_user_notified(self, threshold_brake):
        phone = threshold_brake.threshold.phone
        phone.call()
        phone.handle_user_notified_if_call_succeed()
        assert phone.alarm_message is None


class TestSendUpdateMessage:
    @pytest.mark.xfail(ValidationError)
    def test__send_message__no_alarm_message(self, phone):
        phone.send_telegram_message()
