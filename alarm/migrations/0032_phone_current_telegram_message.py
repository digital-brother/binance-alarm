# Generated by Django 4.1.7 on 2023-06-19 02:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0031_alter_phone_paused_until_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='phone',
            name='current_telegram_message',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
