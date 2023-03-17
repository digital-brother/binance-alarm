from django.contrib import admin

from trading.models import Coin, PhoneNumber


class ThresholdInline(admin.TabularInline):
    model = Coin
    extra = 1


class PhoneNumberAdmin(admin.ModelAdmin):
    inlines = [ThresholdInline]


admin.site.register(PhoneNumber, PhoneNumberAdmin)

admin.site.register(Coin)
