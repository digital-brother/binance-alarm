# Generated by Django 4.1.7 on 2023-06-18 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0027_rename_ringing_twilio_call_sid_phone_twilio_call_sid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phone',
            name='twilio_call_sid',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
