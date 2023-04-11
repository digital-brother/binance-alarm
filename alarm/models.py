import logging

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from alarm.binance_utils import get_binance_trade_pairs

logger = logging.getLogger(f'django.{__name__}')


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = PhoneNumberField(blank=True, unique=True, region='UA')
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.number)


class Threshold(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE)
    trade_pair = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.trade_pair)

    def clean(self):
        super().clean()
        valid_trade_pair = get_binance_trade_pairs()
        if self.trade_pair not in valid_trade_pair:
            raise ValidationError(
                f"{self.trade_pair} is not a valid coin abbreviation. For example, ethusdt or ethbtc.")


class Candle(models.Model):
    # TODO: Possibly extract trade_pair model
    trade_pair = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def last_for_trade_pair(cls, trade_pair):
        return cls.objects.filter(trade_pair=trade_pair).order_by('modified')[-1]

    @classmethod
    def penultimate_for_trade_pair(cls, trade_pair):
        return cls.objects.filter(trade_pair=trade_pair).order_by('modified')[-2]

    @classmethod
    def save_as_recent(cls, trade_pair, high_price, low_price):
        """Deletes old candles, which we do not need anymore"""
        candles_to_delete = cls.objects.filter(trade_pair=trade_pair).order_by('modified')[1:]
        candles_to_delete.delete()

        candle = cls.objects.create(trade_pair=trade_pair, high_price=high_price, low_price=low_price)
        return candle

    def __str__(self):
        return f"{self.trade_pair}: {self.low_price} - {self.high_price} {self.modified}"
