# Generated by Django 4.1.7 on 2023-06-19 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0032_phone_current_telegram_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='phone',
            name='telegram_message_seen',
            field=models.BooleanField(default=False),
        ),
    ]