# Generated by Django 5.2.3 on 2025-06-16 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='session_key',
            field=models.CharField(blank=True, db_index=True, max_length=40, null=True),
        ),
    ]
