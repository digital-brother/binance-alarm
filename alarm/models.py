from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser, User
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


class Candle(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    last_high_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_low_price = models.DecimalField(max_digits=10, decimal_places=2)
