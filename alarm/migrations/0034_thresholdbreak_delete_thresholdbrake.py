# Generated by Django 4.1.7 on 2023-06-25 19:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0033_phone_telegram_message_seen'),
    ]

    operations = [
        migrations.RenameModel('ThresholdBrake', 'ThresholdBreak')
    ]
