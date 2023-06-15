import factory
import decimal
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from alarm.models import Candle, Threshold, Phone, ThresholdBrake

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User


class PhoneFactory(DjangoModelFactory):
    class Meta:
        model = Phone

    user = factory.SubFactory(UserFactory)


class CandleFactory(DjangoModelFactory):
    class Meta:
        model = Candle

    trade_pair = 'lunausdt'
    low_price = decimal.Decimal('12.00')
    high_price = decimal.Decimal('16.00')
    close_price = factory.LazyAttribute(lambda candle: (candle.low_price + candle.high_price) / 2)


class ThresholdFactory(DjangoModelFactory):
    class Meta:
        model = Threshold

    phone = factory.SubFactory(PhoneFactory)
    price = decimal.Decimal("10.00")
    trade_pair = 'lunausdt'


class ThresholdBrakeFactory(DjangoModelFactory):
    class Meta:
        model = ThresholdBrake

    threshold = factory.SubFactory(ThresholdFactory)
