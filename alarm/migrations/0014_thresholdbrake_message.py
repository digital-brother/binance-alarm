# Generated by Django 4.1.7 on 2023-04-26 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0013_thresholdbrake_happened_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='thresholdbrake',
            name='message',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
    ]
