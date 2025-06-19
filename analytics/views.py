from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from analytics.models import SalesAnalytics, CustomerAnalytics, ProductAnalytics, MarketingAnalytics, WebsiteTraffic
from products.models import Product, ProductView
from orders.models import Order, OrderItem
from django.db.models.functions import TruncMonth
from django.core.cache import cache
from functools import wraps
from typing import Optional, Callable, Any
from django.http import HttpRequest, HttpResponse

def generate_cache_key(base_key: str, request: HttpRequest = None, key_func: Optional[Callable] = None, *args, **kwargs) -> str:
    """
    Helper function to generate a cache key consistently across views.
    
    Args:
        base_key (str): The base key for caching.
        request (HttpRequest, optional): The HTTP request object.
        key_func (Callable, optional): A function to generate a dynamic part of the cache key.
        *args, **kwargs: Additional arguments to pass to key_func.
    
    Returns:
        str: The final cache key, combining the base key with a dynamic part if provided.
    """
    if key_func and request:
        dynamic_part = key_func(request, *args, **kwargs)
        return f"{base_key}:{dynamic_part}"
    return base_key


def cache_view(base_key: str, timeout: int = 300, key_func: Optional[Callable] = None) -> Callable:
    """
    A decorator that caches the data context of a view function for a specified duration.
    The HttpResponse is rendered fresh on each request using the cached context to avoid serving stale or user-specific content.
    
    Args:
        base_key (str): The base key used for caching the view data.
        timeout (int, optional): The duration in seconds for which the cache persists. Defaults to 300.
        key_func (Callable, optional): A function to generate a dynamic part of the cache key based on request or arguments. Defaults to None.
    
    Returns:
        Callable: The wrapped view function with caching applied to the data context.
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            final_cache_key = generate_cache_key(base_key, request, key_func, *args, **kwargs)
            cached_context = cache.get(final_cache_key)
            if cached_context is None:
                # Call the view function to get the context dictionary
                result = view_func(request, *args, **kwargs)
                if isinstance(result, dict):
                    cached_context = result
                    cache.set(final_cache_key, cached_context, timeout)
                else:
                    # If the view doesn't return a dict, return the response directly without caching
                    return result
            # Render a fresh response using the cached context
            template_name = getattr(view_func, '__template_name__', 'analytics/dashboard.html')
            return render(request, template_name, cached_context)
        return wrapper
    return decorator


def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
@cache_view('analytics_overview_data', timeout=300, key_func=lambda request, *args, **kwargs: f"user_{request.user.id}")
def dashboard_overview(request):
    # Sales Summary
    last_30_days = timezone.now() - timedelta(days=30)
    sales_data = SalesAnalytics.objects.filter(date__gte=last_30_days).order_by('date')
    total_revenue_30_days = sales_data.aggregate(total=Sum('total_revenue'))['total'] or 0
    total_orders_30_days = sales_data.aggregate(total=Sum('total_orders'))['total'] or 0
    
    # Customer Summary
    customer_data = CustomerAnalytics.objects.filter(date__gte=last_30_days).order_by('date')
    new_customers_30_days = customer_data.aggregate(total=Sum('new_customers'))['total'] or 0
    returning_customers_30_days = customer_data.aggregate(total=Sum('returning_customers'))['total'] or 0
    
    # Product Summary
    top_products = ProductAnalytics.objects.filter(date__gte=last_30_days)\
            .values('product__name')\
            .annotate(total_purchases=Sum('purchase_count'))\
            .order_by('-total_purchases')[:5]
    
    context = {
        'total_revenue_30_days': total_revenue_30_days,
        'total_orders_30_days': total_orders_30_days,
        'new_customers_30_days': new_customers_30_days,
        'returning_customers_30_days': returning_customers_30_days,
        'top_products': list(top_products),
        'sales_data': list(sales_data.values('date', 'total_revenue', 'total_orders')),
        'customer_data': list(customer_data.values('date', 'new_customers', 'returning_customers')),
    }
    return context
dashboard_overview.__template_name__ = 'analytics/dashboard.html'

@login_required
@user_passes_test(is_admin)
@cache_view('analytics_sales_report_data', timeout=300, key_func=lambda request, *args, **kwargs: f"user_{request.user.id}")
def sales_report(request):
    last_365_days = timezone.now() - timedelta(days=365)
    sales_data_daily = SalesAnalytics.objects.filter(date__gte=last_365_days).order_by('date')
    sales_data_monthly = SalesAnalytics.objects.filter(date__gte=last_365_days)\
            .annotate(month=TruncMonth('date'))\
            .values('month')\
            .annotate(total=Sum('total_revenue'), count=Sum('total_orders'))\
            .order_by('-month')[:12]
    
    context = {
        'sales_data_daily': list(sales_data_daily.values('date', 'total_revenue', 'total_orders', 'average_order_value', 'discount_usage_count')),
        'sales_data_monthly': list(sales_data_monthly),
    }
    return context
sales_report.__template_name__ = 'analytics/sales_report.html'

@login_required
@user_passes_test(is_admin)
def customer_insights(request):
    last_365_days = timezone.now() - timedelta(days=365)
    customer_data = CustomerAnalytics.objects.filter(date__gte=last_365_days).order_by('date')
    
    # Calculate aggregates for summary
    total_new_customers = customer_data.aggregate(total=Sum('new_customers'))['total'] or 0
    total_returning_customers = customer_data.aggregate(total=Sum('returning_customers'))['total'] or 0
    avg_retention_rate = customer_data.aggregate(avg=Avg('retention_rate'))['avg'] or 0
    
    context = {
        'customer_data': list(customer_data.values('date', 'new_customers', 'returning_customers', 'retention_rate', 'total_customers')),
        'total_new_customers': total_new_customers,
        'total_returning_customers': total_returning_customers,
        'avg_retention_rate': avg_retention_rate,
    }
    return render(request, 'analytics/customer_insights.html', context)

@login_required
@user_passes_test(is_admin)
def product_performance(request):
    last_30_days = timezone.now() - timedelta(days=30)
    product_data = ProductAnalytics.objects.filter(date__gte=last_30_days)\
            .values('product__name', 'product__id')\
            .annotate(total_views=Sum('views'), total_add_to_cart=Sum('add_to_cart_count'), total_purchases=Sum('purchase_count'))\
            .order_by('-total_purchases')
    
    # Inventory overview
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    out_of_stock_products = Product.objects.filter(stock=0).count()
    
    context = {
        'product_data': list(product_data),
        'low_stock_products': list(low_stock_products),
        'out_of_stock_products': out_of_stock_products,
    }
    return render(request, 'analytics/product_performance.html', context)

@login_required
@user_passes_test(is_admin)
@cache_view('analytics_marketing_data', timeout=300, key_func=lambda request, *args, **kwargs: f"user_{request.user.id}")
def marketing_analysis(request):
    last_90_days = timezone.now() - timedelta(days=90)
    marketing_data = MarketingAnalytics.objects.filter(date__gte=last_90_days).order_by('date')
    
    # Summary by campaign or discount code
    campaign_summary = MarketingAnalytics.objects.filter(date__gte=last_90_days, campaign__isnull=False)\
            .values('campaign__name')\
            .annotate(total_impressions=Sum('impressions'), total_clicks=Sum('clicks'), total_conversions=Sum('conversions'), total_revenue=Sum('revenue_generated'))\
            .order_by('-total_revenue')
    
    discount_summary = MarketingAnalytics.objects.filter(date__gte=last_90_days, discount_code__isnull=False)\
            .values('discount_code')\
            .annotate(total_impressions=Sum('impressions'), total_clicks=Sum('clicks'), total_conversions=Sum('conversions'), total_revenue=Sum('revenue_generated'))\
            .order_by('-total_revenue')
    
    context = {
        'marketing_data': list(marketing_data.values('date', 'impressions', 'clicks', 'conversions', 'revenue_generated', 'click_through_rate', 'conversion_rate')),
        'campaign_summary': list(campaign_summary),
        'discount_summary': list(discount_summary),
    }
    return context
marketing_analysis.__template_name__ = 'analytics/marketing_analysis.html'

@login_required
@user_passes_test(is_admin)
def website_traffic(request):
    last_90_days = timezone.now() - timedelta(days=90)
    traffic_data = WebsiteTraffic.objects.filter(date__gte=last_90_days).order_by('date')
    
    context = {
        'traffic_data': list(traffic_data.values('date', 'total_visits', 'unique_visitors', 'bounce_rate', 'average_session_duration', 'top_referral_source')),
    }
    return render(request, 'analytics/website_traffic.html', context)
