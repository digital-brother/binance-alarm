import requests
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from alarm.binance_utils import get_valid_list_of_symbols


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = PhoneNumberField(blank=True, unique=True, region='UA')
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.number)


class Coin(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, default=None)
    coin_abbreviation = models.CharField(max_length=255, default=None)
    threshold = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.coin_abbreviation)

    def update_or_create_candles(self, current_candle_high_price, current_candle_low_price):
        Candle.objects.update_or_create(
            coin=self,
            defaults={
                'last_high_price': current_candle_high_price,
                'last_low_price': current_candle_low_price,
            },
        )

    def is_valid_coin_abbreviation(self):
        valid_list_of_symbols = get_valid_list_of_symbols()
        return self.coin_abbreviation in valid_list_of_symbols

    def clean(self):
        super().clean()
        if not self.is_valid_coin_abbreviation():
            raise ValidationError(
                f"{self.coin_abbreviation} is not a valid coin abbreviation. For example, ethusdt or ethbtc")


class Candle(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    last_high_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_low_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.coin)
