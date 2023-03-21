from django.contrib import admin

from .models import PhoneNumber, Coin


class CoinInline(admin.TabularInline):
    model = Coin
    extra = 1


class PhoneNumberAdmin(admin.ModelAdmin):
    inlines = [CoinInline]


admin.site.register(PhoneNumber, PhoneNumberAdmin)

admin.site.register(Coin)
