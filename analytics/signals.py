from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from orders.models import Order
from products.models import ProductView
from django.contrib.auth.models import User
from analytics.models import SalesAnalytics, CustomerAnalytics, ProductAnalytics, WebsiteTraffic
from django.db.models import F
from django.db import transaction

@receiver(post_save, sender=Order)
def update_sales_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        sales_analytics, _ = SalesAnalytics.objects.get_or_create(date=today)
        updates = {
            'total_revenue': F('total_revenue') + instance.total_price,
            'total_orders': F('total_orders') + 1
        }
        if instance.discount_code:
            updates['discount_usage_count'] = F('discount_usage_count') + 1
            discount_amount = calculate_discount_amount(instance)
            if discount_amount > 0:
                updates['discount_total_amount'] = F('discount_total_amount') + discount_amount
        with transaction.atomic():
            SalesAnalytics.objects.filter(date=today).update(**updates)
            # Recalculate average_order_value after updates
            SalesAnalytics.objects.filter(date=today).update(
                average_order_value=F('total_revenue') / F('total_orders')
            )

@receiver(post_save, sender=Order)
def update_customer_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        customer_analytics, _ = CustomerAnalytics.objects.get_or_create(date=today)
        user = instance.user
        # Check if user has previous orders to determine if returning customer
        previous_orders_exist = Order.objects.filter(user=user, created_at__lt=instance.created_at).exists()
        updates = {}
        if previous_orders_exist:
            updates['returning_customers'] = F('returning_customers') + 1
        else:
            updates['new_customers'] = F('new_customers') + 1
        with transaction.atomic():
            CustomerAnalytics.objects.filter(date=today).update(**updates)
            # Update total_customers and retention_rate after increments
            CustomerAnalytics.objects.filter(date=today).update(
                total_customers=F('new_customers') + F('returning_customers'),
                retention_rate=(F('returning_customers') / (F('new_customers') + F('returning_customers'))) * 100
            )
        # Customer lifetime value calculation can be refined based on more data

@receiver(post_save, sender=ProductView)
def update_product_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        product = instance.product
        product_analytics, _ = ProductAnalytics.objects.get_or_create(product=product, date=today)
        with transaction.atomic():
            ProductAnalytics.objects.filter(product=product, date=today).update(
                views=F('views') + 1
            )
        # Conversion and abandonment rates to be updated with additional signals if needed

@receiver(post_save, sender=User)
def update_customer_analytics_on_signup(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        customer_analytics, _ = CustomerAnalytics.objects.get_or_create(date=today)
        with transaction.atomic():
            CustomerAnalytics.objects.filter(date=today).update(
                new_customers=F('new_customers') + 1
            )
            CustomerAnalytics.objects.filter(date=today).update(
                total_customers=F('new_customers') + F('returning_customers'),
                retention_rate=(F('returning_customers') / (F('new_customers') + F('returning_customers'))) * 100
            )

# Use Django cache for website traffic updates to reduce database load
from django.core.cache import cache


def calculate_discount_amount(order):
    """
    Calculate the discount amount for an order based on the discount code.
    Returns the discount amount if applicable, otherwise 0.
    """
    if not order.discount_code:
        return 0
    try:
        from promotions.models import DiscountCode
        discount = DiscountCode.objects.get(code=order.discount_code, is_active=True)
        if discount.discount_type == 'fixed_amount':
            return discount.discount_value
        elif discount.discount_type == 'percentage':
            pre_discount_total = sum(item.total_price for item in order.items.all())
            return (pre_discount_total * discount.discount_value) / 100
    except DiscountCode.DoesNotExist:
        return 0
    return 0


def update_website_traffic():
    today = timezone.now().date()
    cache_key = f"website_traffic_{today}"
    # Initialize the cache key with 0 if it doesn't exist
    cache.add(cache_key, 0)
    cache.incr(cache_key)
    # Note: A periodic task should flush this cache to the database
