# Generated by Django 4.1.7 on 2023-03-30 11:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='PhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number',
                 phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region='UA', unique=True)),
                ('pause_service', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Coin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name_coin', models.CharField(max_length=255)),
                ('threshold', models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    'phone_number',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alarm.phonenumber')),
            ],
        ),
    ]
