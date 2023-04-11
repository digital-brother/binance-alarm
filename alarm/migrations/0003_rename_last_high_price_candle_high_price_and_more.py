# Generated by Django 4.1.7 on 2023-04-04 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0002_candle_phone_remove_coin_phone_number_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candle',
            old_name='last_high_price',
            new_name='high_price',
        ),
        migrations.RenameField(
            model_name='candle',
            old_name='last_low_price',
            new_name='low_price',
        ),
        migrations.AlterField(
            model_name='candle',
            name='coin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='last_candle', to='alarm.coin'),
        ),
    ]