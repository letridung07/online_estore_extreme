from django.urls import path
from . import views

app_name = 'social_integration'

urlpatterns = [
    path('platforms/', views.social_platform_list, name='social_platform_list'),
    path('platforms/<int:pk>/update/', views.social_platform_update, name='social_platform_update'),
    path('syncs/', views.product_sync_list, name='product_sync_list'),
    path('sync/<int:product_id>/<int:platform_id>/', views.sync_product, name='sync_product'),
    path('sync/<int:sync_id>/retry/', views.retry_sync, name='retry_sync'),
]
