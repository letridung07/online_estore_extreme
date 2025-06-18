from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from orders.models import Order
from products.models import ProductView
from django.contrib.auth.models import User
from analytics.models import SalesAnalytics, CustomerAnalytics, ProductAnalytics, WebsiteTraffic

@receiver(post_save, sender=Order)
def update_sales_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        sales_analytics, _ = SalesAnalytics.objects.get_or_create(date=today)
        sales_analytics.total_revenue += instance.total_price
        sales_analytics.total_orders += 1
        sales_analytics.average_order_value = sales_analytics.total_revenue / sales_analytics.total_orders
        if instance.discount_code:
            sales_analytics.discount_usage_count += 1
            # Assuming discount amount calculation logic can be added here if available
        sales_analytics.save()

@receiver(post_save, sender=Order)
def update_customer_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        customer_analytics, _ = CustomerAnalytics.objects.get_or_create(date=today)
        user = instance.user
        # Check if user has previous orders to determine if returning customer
        previous_orders = Order.objects.filter(user=user, created_at__lt=instance.created_at).count()
        if previous_orders > 0:
            customer_analytics.returning_customers += 1
        else:
            customer_analytics.new_customers += 1
        customer_analytics.total_customers = customer_analytics.new_customers + customer_analytics.returning_customers
        if customer_analytics.total_customers > 0:
            customer_analytics.retention_rate = (customer_analytics.returning_customers / customer_analytics.total_customers) * 100
        # Customer lifetime value calculation can be refined based on more data
        customer_analytics.save()

@receiver(post_save, sender=ProductView)
def update_product_analytics(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        product = instance.product
        product_analytics, _ = ProductAnalytics.objects.get_or_create(product=product, date=today)
        product_analytics.views += 1
        # Conversion and abandonment rates to be updated with additional signals if needed
        product_analytics.save()

@receiver(post_save, sender=User)
def update_customer_analytics_on_signup(sender, instance, created, **kwargs):
    if created:
        today = timezone.now().date()
        customer_analytics, _ = CustomerAnalytics.objects.get_or_create(date=today)
        customer_analytics.new_customers += 1
        customer_analytics.total_customers = customer_analytics.new_customers + customer_analytics.returning_customers
        if customer_analytics.total_customers > 0:
            customer_analytics.retention_rate = (customer_analytics.returning_customers / customer_analytics.total_customers) * 100
        customer_analytics.save()

# Placeholder for website traffic updates, which may require additional tracking mechanisms
def update_website_traffic():
    today = timezone.now().date()
    traffic, _ = WebsiteTraffic.objects.get_or_create(date=today)
    # Logic for tracking visits and other metrics would be implemented based on request tracking
    traffic.total_visits += 1
    # Additional logic for unique visitors, bounce rate, etc., would be added
    traffic.save()
