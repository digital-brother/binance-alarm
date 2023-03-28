from django.contrib import admin

from .models import Phone, Coin, Candle


class CoinInline(admin.TabularInline):
    model = Coin
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [CoinInline]


admin.site.register(Phone, PhoneAdmin)

admin.site.register(Coin)

admin.site.register(Candle)
