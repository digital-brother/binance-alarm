import factory
import decimal
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from alarm.models import Candle, Threshold, Phone, ThresholdBreak

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")


class PhoneFactory(DjangoModelFactory):
    class Meta:
        model = Phone

    user = factory.SubFactory(UserFactory)
    number = factory.Sequence(lambda n: f"+38 123 456 78 {n}")
    telegram_chat_id = factory.Sequence(lambda n: f"telegram_user_{n}")
    enabled = True


class CandleFactory(DjangoModelFactory):
    class Meta:
        model = Candle

    trade_pair = 'LUNAUSDT'
    low_price = decimal.Decimal('12.00')
    high_price = decimal.Decimal('16.00')
    close_price = factory.LazyAttribute(lambda candle: (candle.low_price + candle.high_price) / 2)


class ThresholdFactory(DjangoModelFactory):
    class Meta:
        model = Threshold

    phone = factory.SubFactory(PhoneFactory)
    price = decimal.Decimal("10.00")
    trade_pair = 'LUNAUSDT'


class ThresholdBreakFactory(DjangoModelFactory):
    class Meta:
        model = ThresholdBreak

    threshold = factory.SubFactory(ThresholdFactory)
