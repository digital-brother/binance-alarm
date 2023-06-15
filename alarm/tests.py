import decimal

import pytest
from decimal import Decimal
from pytest_factoryboy import register

from alarm.factories import ThresholdFactory, CandleFactory, ThresholdBrakeFactory, PhoneFactory, UserFactory
from alarm.models import TradePair, ThresholdBrake

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
        trade_pair = 'lunausdt'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 1
        assert ThresholdBrake.objects.first().threshold == threshold


    def test__create_threshold_brake__does_not_create_duplicate(self):
        trade_pair = 'lunausdt'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        ThresholdBrakeFactory(threshold=threshold)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 1


    def test__create_threshold_brake__threshold_not_broken(self):
        trade_pair = 'lunausdt'
        ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
        assert ThresholdBrake.objects.count() == 0


class TestTradePairAlarmMessage:
    def test__trade_pair_alarm_message__no_threshold_brakes(self, phone):
        trade_pair_obj = TradePair(phone=phone, trade_pair='lunausdt')
        assert trade_pair_obj.alarm_message is None

    def test__trade_pair_alarm_message__single_threshold_brake(self):
        threshold_brake = ThresholdBrakeFactory()
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_brake.threshold.phone, trade_pair=threshold_brake.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA/USDT broken thresholds 10.00$ and the current LUNA/USDT price is 14.00$.'

    def test__trade_pair_alarm_message__another_trade_pair_threshold_brake_not_shown(self, threshold_brake):
        wing_threshold = ThresholdFactory(trade_pair='wingusdt', phone=threshold_brake.threshold.phone)
        ThresholdBrakeFactory(threshold=wing_threshold)
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_brake.threshold.phone, trade_pair=threshold_brake.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA/USDT broken thresholds 10.00$ and the current LUNA/USDT price is 14.00$.'

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
               'LUNA/USDT broken thresholds 10.00$, 12.00$, 10.00$ and the current LUNA/USDT price is 14.00$.'


class TestPhoneAlarmMessage:
    def test__phone_alarm_message__no_brakes(self, phone):
        assert phone.alarm_message is None

    def test__phone_alarm_message__single_trade_pair_broken(self, threshold_brake, candle):
        assert threshold_brake.threshold.phone.alarm_message == \
               'LUNA/USDT broken thresholds 10.00$ and the current LUNA/USDT price is 14.00$.'

    def test__phone_alarm_message__two_trade_pairs_broken(self, threshold_brake, candle):
        threshold_two = ThresholdFactory(trade_pair='wingusdt', price='20.00', phone=threshold_brake.threshold.phone)
        CandleFactory(trade_pair='wingusdt', close_price=decimal.Decimal('24.00'))
        ThresholdBrakeFactory(threshold=threshold_two)
        assert threshold_brake.threshold.phone.alarm_message == \
               'LUNA/USDT broken thresholds 10.00$ and the current LUNA/USDT price is 14.00$.\n' \
               'WING/USDT broken thresholds 20.00$ and the current WING/USDT price is 24.00$.'
