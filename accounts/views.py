from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile, ShippingAddress
from orders.models import Order

@login_required
def profile(request):
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    shipping_addresses = user.shipping_addresses.all()
    orders = user.orders.all().order_by('-created_at')
    
    context = {
        'user': user,
        'profile': profile,
        'shipping_addresses': shipping_addresses,
        'orders': orders,
    }
    return render(request, 'accounts/profile.html', context)
