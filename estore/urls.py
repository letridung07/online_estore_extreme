"""
URL configuration for estore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import profile, add_shipping_address, edit_shipping_address, edit_profile, email_preferences, delete_shipping_address, wishlist, add_to_wishlist, remove_from_wishlist, move_to_cart

urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/profile/add-address/', add_shipping_address, name='add_shipping_address'),
    path('accounts/profile/edit-address/<int:address_id>/', edit_shipping_address, name='edit_shipping_address'),
    path('accounts/profile/delete-address/<int:address_id>/', delete_shipping_address, name='delete_shipping_address'),
    path('accounts/profile/edit/', edit_profile, name='edit_profile'),
    path('accounts/profile/email-preferences/', email_preferences, name='email_preferences'),
    path('accounts/wishlist/', wishlist, name='wishlist'),
    path('accounts/wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('accounts/wishlist/remove/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('accounts/wishlist/move-to-cart/<int:item_id>/', move_to_cart, name='move_to_cart'),
    path('promotions/', include('promotions.urls')),
]
