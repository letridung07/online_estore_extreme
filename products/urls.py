from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('compare/add/<int:product_id>/', views.add_to_comparison, name='add_to_comparison'),
    path('compare/remove/<int:product_id>/', views.remove_from_comparison, name='remove_from_comparison'),
    path('compare/clear/', views.clear_comparison, name='clear_comparison'),
    path('compare/', views.compare_products, name='compare_products'),
]
