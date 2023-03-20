from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class PhoneNumberManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError('Users must have a phone number')

        user = self.model(phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password):
        user = self.create_user(phone_number=phone_number, password=password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class PhoneNumber(AbstractBaseUser, PermissionsMixin):
    phone_number = PhoneNumberField(blank=True, unique=True, region='UA')
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    pause_service = models.BooleanField(default=False)

    objects = PhoneNumberManager()

    USERNAME_FIELD = 'phone_number'

    def __str__(self):
        return str(self.phone_number)


class Coin(models.Model):
    phone_number = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)
    short_name_coin = models.CharField(max_length=255)
    threshold = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.short_name_coin)
