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
from .models import ShippingAddress, UserProfile

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

@login_required
def edit_shipping_address(request, address_id):
    address = ShippingAddress.objects.get(id=address_id, user=request.user)
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            # If this is set as default, unset any other default addresses
            if updated_address.is_default:
                request.user.shipping_addresses.exclude(id=updated_address.id).update(is_default=False)
            updated_address.save()
            return redirect('profile')
    else:
        form = ShippingAddressForm(instance=address)
    return render(request, 'accounts/add_address.html', {'form': form, 'editing': True, 'address_id': address_id})

from django.contrib.auth.forms import UserChangeForm

class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileDetailsForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'phone_number']

@login_required
def edit_profile(request):
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileDetailsForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = ProfileDetailsForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)
