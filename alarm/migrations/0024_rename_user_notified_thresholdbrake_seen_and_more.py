# Generated by Django 4.1.7 on 2023-06-16 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0023_alter_phone_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='thresholdbrake',
            old_name='user_notified',
            new_name='seen',
        ),
        migrations.AlterField(
            model_name='thresholdbrake',
            name='threshold',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unseen_threshold_brakes', to='alarm.threshold'),
        ),
    ]
