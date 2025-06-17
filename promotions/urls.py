from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    path('apply-discount/', views.apply_discount_code, name='apply_discount'),
    path('remove-discount/', views.remove_discount_code, name='remove_discount'),
    path('current/', views.current_promotions, name='current_promotions'),
]
