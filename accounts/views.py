from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile, ShippingAddress, Wishlist, WishlistItem
from orders.models import Order
from products.models import Product
from django.contrib import messages

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
        fields = ['full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'is_default']

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
        fields = ['bio', 'phone_number']

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

@login_required
def email_preferences(request):
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        newsletter = request.POST.get('newsletter') == 'on'
        promotional = request.POST.get('promotional_emails') == 'on'
        profile.newsletter_subscription = newsletter
        profile.promotional_emails = promotional
        profile.save()
        return redirect('profile')
    else:
        context = {
            'user': user,
            'profile': profile,
        }
        return render(request, 'accounts/email_preferences.html', context)

@login_required
def delete_shipping_address(request, address_id):
    try:
        address = ShippingAddress.objects.get(id=address_id, user=request.user)
        address.delete()
    except ShippingAddress.DoesNotExist:
        pass  # Address not found or not owned by user, silently redirect
    return redirect('profile')

@login_required
def wishlist(request):
    user = request.user
    try:
        wishlist = user.wishlist.get()
    except Wishlist.DoesNotExist:
        wishlist = Wishlist.objects.create(user=user)
    
    wishlist_items = wishlist.items.all().order_by('-added_at')
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'accounts/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    user = request.user
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist = user.wishlist.get()
    except Wishlist.DoesNotExist:
        wishlist = Wishlist.objects.create(user=user)
    
    response_data = {}
    if not WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        messages.success(request, f"{product.name} has been added to your wishlist.")
        response_data['status'] = 'added'
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
        response_data['status'] = 'exists'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(response_data)
    return redirect(request.META.get('HTTP_REFERER', 'product_detail'), pk=product_id)

@login_required
def remove_from_wishlist(request, item_id):
    user = request.user
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=user)
    product_name = wishlist_item.product.name
    wishlist_item.delete()
    messages.success(request, f"{product_name} has been removed from your wishlist.")
    return redirect('wishlist')

@login_required
def move_to_cart(request, item_id):
    from cart.models import Cart, CartItem
    user = request.user
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=user)
    product = wishlist_item.product
    
    try:
        cart = user.carts.get()
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 1})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    wishlist_item.delete()
    messages.success(request, f"{product.name} has been moved to your cart.")
    return redirect('wishlist')
