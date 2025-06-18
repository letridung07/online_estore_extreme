from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from products.models import Product, ProductView
from orders.models import Order, OrderItem
from django.db.models.functions import TruncDay, TruncMonth
from django.db.models import Avg
from django.core.cache import cache

ORDER_STATUSES = ['processing', 'shipped', 'delivered']

def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Sales Trends
    last_30_days = timezone.now() - timedelta(days=30)
    sales_data = Order.objects.filter(created_at__gte=last_30_days, status__in=ORDER_STATUSES)\
        .annotate(day=TruncDay('created_at'))\
        .values('day')\
        .annotate(total=Sum('total_price'))\
        .order_by('day')

    monthly_sales = Order.objects.filter(status__in=ORDER_STATUSES)\
        .annotate(month=TruncMonth('created_at'))\
        .values('month')\
        .annotate(total=Sum('total_price'))\
        .order_by('month')[:12]

    # Popular Products
    top_products = OrderItem.objects.filter(order__status__in=ORDER_STATUSES)\
        .values('product__name')\
        .annotate(total_quantity=Sum('quantity'))\
        .order_by('-total_quantity')[:5]

    most_viewed = ProductView.objects.values('product__name')\
        .annotate(view_count=Count('id'))\
        .order_by('-view_count')[:5]
    # User Engagement

    avg_rating = Product.objects.filter(reviews__isnull=False)\
        .aggregate(avg_rating=Avg('reviews__rating'))

    total_views = cache.get('total_views_count')
    if total_views is None:
        total_views = ProductView.objects.count()
        cache.set('total_views_count', total_views, 300)  # cache for 5 minutes

    total_reviews = Product.objects.filter(reviews__isnull=False).count()

    # Inventory Overview
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    out_of_stock_products = Product.objects.filter(stock=0).count()

    context = {
        'sales_data': list(sales_data),
        'monthly_sales': list(monthly_sales),
        'top_products': list(top_products),
        'most_viewed': list(most_viewed),
        'avg_rating': avg_rating.get('avg_rating', 0),
        'total_views': total_views,
        'total_reviews': total_reviews,
        'low_stock_products': list(low_stock_products),
        'out_of_stock_products': out_of_stock_products,
    }
    return render(request, 'analytics/dashboard.html', context)
