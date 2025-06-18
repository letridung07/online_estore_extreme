from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from orders.models import Order
from products.models import ProductView
from django.contrib.auth.models import User
from analytics.models import SalesAnalytics, CustomerAnalytics, ProductAnalytics, WebsiteTraffic
from django.db.models import F
from django.db import transaction
from django.db.models import Case, When, Value, FloatField, Func, DecimalField
from promotions.models import DiscountCode
from django_redis import get_redis_connection
import logging

# Set up logging for analytics signals
logger = logging.getLogger('analytics.signals')

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
            # Combine all updates into a single operation to reduce database queries
            updates['average_order_value'] = calculate_average_order_value(F('total_revenue'), F('total_orders'))
            SalesAnalytics.objects.filter(date=today).update(**updates)

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
            update_customer_metrics(today)
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
            update_customer_metrics(today)

def calculate_average_order_value(total_revenue, total_orders):
    """
    Calculate the average order value given total revenue and total orders.
    Returns the average order value rounded to 2 decimal places, or 0.0 if no orders exist.
    """
    return Case(
        When(total_orders__gt=0, then=Func(total_revenue / total_orders, function='ROUND', template='%(function)s(%(expressions)s, 2)', output_field=DecimalField(decimal_places=2, max_digits=10))),
        default=Value(0.0, output_field=DecimalField(decimal_places=2, max_digits=10))
    )

def update_customer_metrics(date):
    """
    Helper function to update total_customers and retention_rate for CustomerAnalytics.
    This centralizes the logic to avoid duplication.
    """
    CustomerAnalytics.objects.filter(date=date).update(
        total_customers=F('new_customers') + F('returning_customers'),
        retention_rate=Case(
            When(total_customers__gt=0, then=(F('returning_customers') / F('total_customers')) * 100),
            default=Value(0.0, output_field=FloatField())
        )
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
        discount = DiscountCode.objects.get(code=order.discount_code, is_active=True)
        if discount.discount_type == 'fixed_amount':
            return discount.discount_value
        elif discount.discount_type == 'percentage':
            pre_discount_total = sum(item.total_price for item in order.items.all())
            return (pre_discount_total * discount.discount_value) / 100
    except DiscountCode.DoesNotExist:
        logger.warning(f"Discount code not found: {order.discount_code} for order ID: {order.id}")
        return 0
    return 0


def update_website_traffic(visitor_id='unknown', request=None):
    today = timezone.now().date()
    total_visits_key = f"website_traffic_total_{today}"
    unique_visitors_key = f"website_traffic_unique_{today}"
    bounces_key = f"website_traffic_bounces_{today}"
    
    # Initialize cache keys if they don't exist for total visits and bounces
    cache.add(total_visits_key, 0)
    cache.add(bounces_key, 0)
    
    # Increment total visits using atomic operation
    cache.incr(total_visits_key)
    
    # Track unique visitors using Redis atomic set operation
    redis_conn = get_redis_connection("default")
    redis_conn.sadd(unique_visitors_key, visitor_id)
    
    # Track bounce rate (single-page visits)
    if request:
        session = request.session
        session_key = f"visited_pages_{visitor_id}_{today}"
        if session_key not in session:
            session[session_key] = [request.path_info]
            session.modified = True
            # Assume potential bounce on first page visit
            cache.incr(bounces_key)
        else:
            visited_pages = session[session_key]
            if len(visited_pages) == 1 and request.path_info not in visited_pages:
                # Visitor navigated to a second page, not a bounce, so decrement bounce count
                visited_pages.append(request.path_info)
                session[session_key] = visited_pages
                session.modified = True
                # Safeguard to prevent negative bounce count
                current_bounces = cache.get(bounces_key, 0)
                if current_bounces > 0:
                    cache.decr(bounces_key)
            elif len(visited_pages) == 1:
                # Still on first page, potential bounce already counted
                pass
            # Bounce count adjustment for sessions that timeout without navigating to a second page
            # is handled by a periodic task 'check_inactive_sessions' which checks session data for inactivity (e.g., 30 minutes).
    
    # Note: A periodic task should flush these cache values to the database, including using scard for unique visitors count
