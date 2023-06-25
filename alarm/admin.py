from django.contrib import admin

from .models import Phone, Threshold, Candle, ThresholdBreak


class CoinInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [CoinInline]


# TODO: Make trade pair to be entered with no USDT prefix
class ThresholdBreakAdmin(admin.ModelAdmin):
    model = ThresholdBreak
    readonly_fields = ['id', 'threshold_id', 'happened_at']
    list_display = ['phone', '__str__', 'seen']

    @admin.display(description="Phone")
    def phone(self, obj):
        return obj.threshold.phone


admin.site.register(Phone, PhoneAdmin)

admin.site.register(Threshold)

admin.site.register(Candle)

admin.site.register(ThresholdBreak, ThresholdBreakAdmin)
