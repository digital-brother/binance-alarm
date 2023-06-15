import factory

from alarm.models import Candle, Threshold


class CandleFactory(factory.Factory):
    class Meta:
        model = Candle


class ThresholdFactory(factory.Factory):
    class Meta:
        model = Threshold
