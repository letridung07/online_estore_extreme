# Generated by Django 5.2.3 on 2025-06-17 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_shippingmethod_order_shipping_method'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='shipping_method',
        ),
    ]
