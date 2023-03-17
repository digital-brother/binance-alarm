from django.contrib import admin

from trading.models import Coin, PhoneNumber

admin.site.register(PhoneNumber)

admin.site.register(Coin)