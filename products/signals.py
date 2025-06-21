from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, Variant, StockAlert
from .notifications import send_low_stock_notification
from .reordering import initiate_reorder


def create_stock_alert_if_needed(alert_type, instance, stock_level):
    """
    Helper function to check for existing pending stock alerts and create a new one if needed.
    Args:
        alert_type (str): Type of alert ('product' or 'variant')
        instance: The Product or Variant instance
        stock_level (int): Current stock level
    Returns:
        StockAlert: The created or existing alert, or None if no alert was created
    """
    recent_alert = None
    if alert_type == 'product':
        recent_alert = StockAlert.objects.filter(
            alert_type='product',
            product=instance,
            status='pending'
        ).order_by('-created_at').first()
    elif alert_type == 'variant':
        recent_alert = StockAlert.objects.filter(
            alert_type='variant',
            variant=instance,
            status='pending'
        ).order_by('-created_at').first()

    if not recent_alert:
        alert_data = {
            'alert_type': alert_type,
            'stock_level': stock_level,
            'status': 'pending'
        }
        if alert_type == 'product':
            alert_data['product'] = instance
        elif alert_type == 'variant':
            alert_data['variant'] = instance
            
        alert = StockAlert.objects.create(**alert_data)
        send_low_stock_notification(alert)
        if alert_type == 'product':
            initiate_reorder(alert)
        return alert
    return None

@receiver(post_save, sender=Product)
def check_product_stock(sender, instance, **kwargs):
    """
    Signal handler to check stock levels for a Product after it's saved.
    Creates a StockAlert if stock is below the low_stock_threshold and no recent alert exists.
    """
    if instance.stock < instance.low_stock_threshold:
        create_stock_alert_if_needed('product', instance, instance.stock)

@receiver(post_save, sender=Variant)
def check_variant_stock(sender, instance, **kwargs):
    """
    Signal handler to check stock levels for a Variant after it's saved.
    Creates a StockAlert if stock is below the low_stock_threshold and no recent alert exists.
    """
    if instance.stock < instance.low_stock_threshold:
        create_stock_alert_if_needed('variant', instance, instance.stock)
