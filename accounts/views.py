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

from django.forms import ModelForm
from .models import ShippingAddress

class ShippingAddressForm(ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['street', 'city', 'state', 'zip_code', 'country', 'is_default']

@login_required
def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If this is set as default, unset any other default addresses
            if address.is_default:
                request.user.shipping_addresses.exclude(id=address.id).update(is_default=False)
            address.save()
            return redirect('profile')
    else:
        form = ShippingAddressForm()
    return render(request, 'accounts/add_address.html', {'form': form})
