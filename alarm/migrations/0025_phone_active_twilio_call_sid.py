# Generated by Django 4.1.7 on 2023-06-16 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0024_rename_user_notified_thresholdbrake_seen_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='phone',
            name='active_twilio_call_sid',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
    ]
