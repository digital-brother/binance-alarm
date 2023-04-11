from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from phonenumber_field.modelfields import PhoneNumberField

from alarm.binance_utils import get_binance_trade_pairs


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

    @property
    def get_last_candle(self):
        """Returns the last candle object associated with this coin."""
        return self.candle.filter(coin=self).last()

    @property
    def last_high_price(self):
        """Returns the high price of the last candle object associated with this coin."""
        last_candle = self.get_last_candle
        if last_candle:
            return last_candle.high_price
        else:
            return None

    @property
    def last_low_price(self):
        """Returns the low price of the last candle object associated with this coin."""
        last_candle = self.get_last_candle
        if last_candle:
            return last_candle.low_price
        else:
            return None

    def clean(self):
        super().clean()
        list_of_binance_coins_abbreviations = get_binance_trade_pairs()
        if self.trade_pair not in list_of_binance_coins_abbreviations:
            raise ValidationError(
                f"{self.trade_pair} is not a valid coin abbreviation. For example, ethusdt or ethbtc")


class Candle(models.Model):
    # TODO: Possibly extract trade_pair model
    trade_pair = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def update_or_create(cls, trade_pair, current_candle_high_price, current_candle_low_price):
        candle = cls.objects.update_or_create(
            trade_pair=trade_pair,
            defaults={
                'high_price': current_candle_high_price,
                'low_price': current_candle_low_price,
            },
        )
        print(f"Candle updated: {candle}")
        return candle[0]

    def __str__(self):
        return f"{self.trade_pair}: {self.low_price} - {self.high_price} {self.modified}"
