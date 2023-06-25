from django.contrib import admin

from .models import Phone, Threshold, Candle, ThresholdBreak


class ThresholdInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [ThresholdInline]

    def save_model(self, request, phone, form, change):
        paused_until_changed = None
        if change:
            old_phone = Phone.objects.get(pk=phone.pk)
            if phone.paused_until != old_phone.paused_until:
                paused_until_changed = True

        phone.save()
        if paused_until_changed:
            phone.send_phone_paused_telegram_message()


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
