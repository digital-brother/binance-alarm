import pytest
from decimal import Decimal

from alarm.factories import ThresholdFactory, CandleFactory, ThresholdBrakeFactory
from alarm.models import TradePair, ThresholdBrake

pytestmark = pytest.mark.django_db


def test__threshold_is_broken__single_candle():
    threshold = ThresholdFactory(price=Decimal('10.00'))
    candle = CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'))
    assert threshold.is_broken(None, candle)


def test__threshold_not_broken__single_candle():
    threshold = ThresholdFactory(price=Decimal('10.00'))
    candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
    assert not threshold.is_broken(None, candle)


def test__threshold_is_broken__two_candles():
    threshold = ThresholdFactory(price=Decimal('10.00'))
    first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('9.00'))
    second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('11.00'))
    assert threshold.is_broken(first_candle, second_candle)


def test__threshold_not_broken__two_candles():
    threshold = ThresholdFactory(price=Decimal('10.00'))
    first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
    second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
    assert not threshold.is_broken(first_candle, second_candle)


def test__threshold_is_broken__two_candles_with_gap():
    threshold = ThresholdFactory(price=Decimal('10.00'))
    first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
    second_candle = CandleFactory(low_price=Decimal('12.00'), high_price=Decimal('13.00'))
    assert threshold.is_broken(first_candle, second_candle)


def test__create_threshold_brake__threshold_broken():
    trade_pair = 'lunausdt'
    threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
    CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
    TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
    assert ThresholdBrake.objects.count() == 1
    assert ThresholdBrake.objects.first().threshold == threshold


def test__create_threshold_brake__does_not_create_duplicate():
    trade_pair = 'lunausdt'
    threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
    CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
    ThresholdBrakeFactory(threshold=threshold)
    TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
    assert ThresholdBrake.objects.count() == 1


def test__create_threshold_brake__threshold_not_broken():
    trade_pair = 'lunausdt'
    ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
    CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'), trade_pair=trade_pair)
    TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)
    assert ThresholdBrake.objects.count() == 0
