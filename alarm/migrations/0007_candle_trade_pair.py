# Generated by Django 4.1.7 on 2023-04-10 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0006_rename_threshold_threshold_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='candle',
            name='trade_pair',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
