from django.contrib import admin

from trading.models import Coin, CustomUser

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Coin)
