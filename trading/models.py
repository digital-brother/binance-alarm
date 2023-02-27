from django.db import models


class UserSetting(models.Model):
    phone_number = models.CharField(max_length=20)
    coin = models.CharField(max_length=10)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)