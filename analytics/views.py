from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from analytics.models import SalesAnalytics, CustomerAnalytics, ProductAnalytics, MarketingAnalytics, WebsiteTraffic
from products.models import Product, ProductView
from orders.models import Order, OrderItem
from django.db.models.functions import TruncDay, TruncMonth
from django.core.cache import cache
from functools import wraps

def cache_view(cache_key, timeout=300, key_func=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            final_cache_key = cache_key
            if key_func:
                dynamic_part = key_func(request, *args, **kwargs)
                final_cache_key = f"{cache_key}:{dynamic_part}"
            context = cache.get(final_cache_key)
            if context is None:
                context = view_func(request, *args, **kwargs)
                cache.set(final_cache_key, context, timeout)
            return context
        return wrapper
    return decorator

ORDER_STATUSES = ['processing', 'shipped', 'delivered']

def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
@cache_view('analytics_overview_data', timeout=300)
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
    return render(request, 'analytics/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@cache_view('analytics_sales_report_data', timeout=300)
def sales_report(request):
    last_365_days = timezone.now() - timedelta(days=365)
    sales_data_daily = SalesAnalytics.objects.filter(date__gte=last_365_days).order_by('date')
    sales_data_monthly = SalesAnalytics.objects.filter(date__gte=last_365_days)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('total_revenue'), count=Sum('total_orders'))\
        .order_by('month')[:12]
    
    context = {
        'sales_data_daily': list(sales_data_daily.values('date', 'total_revenue', 'total_orders', 'average_order_value', 'discount_usage_count')),
        'sales_data_monthly': list(sales_data_monthly),
    }
    return render(request, 'analytics/sales_report.html', context)

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
    return render(request, 'analytics/marketing_analysis.html', context)

@login_required
@user_passes_test(is_admin)
def website_traffic(request):
    last_90_days = timezone.now() - timedelta(days=90)
    traffic_data = WebsiteTraffic.objects.filter(date__gte=last_90_days).order_by('date')
    
    context = {
        'traffic_data': list(traffic_data.values('date', 'total_visits', 'unique_visitors', 'bounce_rate', 'average_session_duration', 'top_referral_source')),
    }
    return render(request, 'analytics/website_traffic.html', context)
