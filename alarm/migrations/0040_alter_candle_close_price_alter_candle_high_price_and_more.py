# Generated by Django 4.1.7 on 2023-06-25 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0039_alter_threshold_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candle',
            name='close_price',
            field=models.DecimalField(decimal_places=4, max_digits=10),
        ),
        migrations.AlterField(
            model_name='candle',
            name='high_price',
            field=models.DecimalField(decimal_places=4, max_digits=10),
        ),
        migrations.AlterField(
            model_name='candle',
            name='low_price',
            field=models.DecimalField(decimal_places=4, max_digits=10),
        ),
    ]
