from django.contrib import admin

from trading.models import SearchCoin, CreatePhoneNumber


class CreatePhoneNumberAdmin(admin.ModelAdmin):
    exclude = ('is_staff', 'is_superuser', 'is_admin', 'user_permissions', 'groups', 'last_login', 'password')


admin.site.register(CreatePhoneNumber, CreatePhoneNumberAdmin)

admin.site.register(SearchCoin)
