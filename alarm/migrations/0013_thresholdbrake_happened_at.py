# Generated by Django 4.1.7 on 2023-04-25 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0012_remove_thresholdbrake_happened_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='thresholdbrake',
            name='happened_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
