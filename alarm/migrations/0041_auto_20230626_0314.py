# Generated by Django 4.1.7 on 2023-06-26 00:14
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import migrations


def add_user_group(apps, schema_editor):
    # Access the models using the apps module
    Phone = apps.get_model('alarm', 'Phone')
    phone_content_type = ContentType.objects.get_for_model(Phone)
    phone_permissions = Permission.objects.filter(content_type=phone_content_type)

    user_group = Group.objects.get_or_create(name='User')[0]
    user_group.permissions.add(*phone_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0040_alter_candle_close_price_alter_candle_high_price_and_more'),
    ]

    operations = [
        migrations.RunPython(add_user_group),
    ]
