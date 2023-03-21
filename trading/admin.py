from django.contrib import admin

from trading.models import Coin, PhoneNumber


class PhoneNumberAdmin(admin.ModelAdmin):
    exclude = ('is_staff', 'is_superuser', 'is_admin', 'user_permissions', 'groups', 'last_login', 'password')


admin.site.register(PhoneNumber, PhoneNumberAdmin)

admin.site.register(Coin)
