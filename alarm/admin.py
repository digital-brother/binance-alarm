from django.contrib import admin

from .models import Phone, Threshold, Candle, ThresholdBrake


class CoinInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [CoinInline]


# TODO: Make trade pair to be entered with no USDT prefix
class ThresholdBrakeAdmin(admin.ModelAdmin):
    model = ThresholdBrake
    readonly_fields = ['id', 'threshold_id', 'happened_at', 'seen']


admin.site.register(Phone, PhoneAdmin)

admin.site.register(Threshold)

admin.site.register(Candle)

admin.site.register(ThresholdBrake, ThresholdBrakeAdmin)
