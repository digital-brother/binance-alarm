from django.contrib import admin
from django.utils import timezone

from . import telegram_utils
from .models import Phone, Threshold, Candle, ThresholdBreak


class ThresholdInline(admin.TabularInline):
    model = Threshold
    extra = 1


class PhoneAdmin(admin.ModelAdmin):
    inlines = [ThresholdInline]
    list_display = ['__str__', 'user']
    readonly_fields = [
        'twilio_call_sid',
        'telegram_message_id',
        'current_telegram_message',
        'telegram_message_seen'
    ]

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            fields = super().get_fields(request, obj)
            return fields
        return ['user', 'number', 'telegram_chat_id', 'pause_minutes_duration', 'paused_until', 'enabled']

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return self.model.objects.filter(user=request.user)

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


class ThresholdAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'phone_user']

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return self.model.objects.filter(phone__user=request.user)

    def phone_user(self, obj):
        return obj.phone.user
    phone_user.short_description = 'User'


# TODO: Make trade pair to be entered with no USDT prefix
class ThresholdBreakAdmin(admin.ModelAdmin):
    model = ThresholdBreak
    readonly_fields = ['id', 'threshold_id', 'happened_at']
    list_display = ['__str__', 'phone', 'seen']

    @admin.display(description="Phone")
    def phone(self, obj):
        return obj.threshold.phone


admin.site.register(Phone, PhoneAdmin)

admin.site.register(Threshold, ThresholdAdmin)

admin.site.register(Candle)

admin.site.register(ThresholdBreak, ThresholdBreakAdmin)
