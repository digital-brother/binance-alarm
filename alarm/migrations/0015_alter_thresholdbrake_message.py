# Generated by Django 4.1.7 on 2023-04-26 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0014_thresholdbrake_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thresholdbrake',
            name='message',
            field=models.TextField(default=None),
        ),
    ]
