import requests
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = PhoneNumberField(blank=True, unique=True, region='UA')
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.number)


class Coin(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE)
    coin_abbreviation = models.CharField(max_length=255)
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

    def get_valid_list_of_symbols(self):
        BINANCE_API_URL = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(BINANCE_API_URL)

        if response.status_code == 200:
            valid_list_of_symbols = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
            return valid_list_of_symbols
        else:
            return []

    def is_valid_coin_abbreviation(self):
        valid_list_of_symbols = self.get_valid_list_of_symbols()
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
