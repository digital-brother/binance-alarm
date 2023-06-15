from decimal import Decimal

from alarm.factories import ThresholdFactory, CandleFactory


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