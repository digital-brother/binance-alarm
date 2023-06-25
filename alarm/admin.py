from django.contrib import admin
from django.utils import timezone

from . import telegram_utils
from .models import Phone, Threshold, Candle, ThresholdBreak


class ThresholdInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [ThresholdInline]
    readonly_fields = [
        'twilio_call_sid',
        'telegram_message_id',
        'current_telegram_message',
        'telegram_message_seen'
    ]

    def save_model(self, request, phone, form, change):
        paused_until_changed = None
        if change:
            old_phone = Phone.objects.get(pk=phone.pk)
            if phone.paused_until != old_phone.paused_until:
                paused_until_changed = True
        phone.save()

        if paused_until_changed:
            paused_until_str = timezone.localtime(phone.paused_until).strftime("%Y-%m-%d %H:%M:%S")
            bot_paused_message = f'Bot was paused until {paused_until_str}.'
            telegram_utils.send_message(phone.telegram_chat_id, bot_paused_message)


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
