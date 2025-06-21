from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, Variant, StockAlert
from .notifications import send_low_stock_notification
from .reordering import initiate_reorder

@receiver(post_save, sender=Product)
def check_product_stock(sender, instance, **kwargs):
    """
    Signal handler to check stock levels for a Product after it's saved.
    Creates a StockAlert if stock is below the low_stock_threshold and no recent alert exists.
    """
    if instance.stock < instance.low_stock_threshold:
        # Check if there's already a pending alert for this product
        recent_alert = StockAlert.objects.filter(
            alert_type='product',
            product=instance,
            status='pending'
        ).order_by('-created_at').first()
        
        if not recent_alert:
            alert = StockAlert.objects.create(
                alert_type='product',
                product=instance,
                stock_level=instance.stock,
                status='pending'
            )
            send_low_stock_notification(alert)
            initiate_reorder(alert)

@receiver(post_save, sender=Variant)
def check_variant_stock(sender, instance, **kwargs):
    """
    Signal handler to check stock levels for a Variant after it's saved.
    Creates a StockAlert if stock is below the low_stock_threshold and no recent alert exists.
    """
    if instance.stock < instance.low_stock_threshold:
        # Check if there's already a pending alert for this variant
        recent_alert = StockAlert.objects.filter(
            alert_type='variant',
            variant=instance,
            status='pending'
        ).order_by('-created_at').first()
        
        if not recent_alert:
            alert = StockAlert.objects.create(
                alert_type='variant',
                variant=instance,
                stock_level=instance.stock,
                status='pending'
            )
            send_low_stock_notification(alert)
