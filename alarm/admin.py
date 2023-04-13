from django.contrib import admin

from .models import Phone, Threshold, Candle, ThresholdBrake


class CoinInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [CoinInline]


admin.site.register(Phone, PhoneAdmin)

admin.site.register(Threshold)

admin.site.register(Candle)

admin.site.register(ThresholdBrake)
