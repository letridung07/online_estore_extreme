from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard_overview, name='dashboard'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('customer-insights/', views.customer_insights, name='customer_insights'),
    path('product-performance/', views.product_performance, name='product_performance'),
    path('marketing-analysis/', views.marketing_analysis, name='marketing_analysis'),
    path('website-traffic/', views.website_traffic, name='website_traffic'),
]
