from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product
from django.contrib.auth.decorators import login_required

def cart_detail(request):
    cart = get_cart(request)
    discount_code = request.session.get('discount_code')
    discount_amount = 0
    discounted_total = cart.total_price

    if discount_code:
        from orders.helpers import apply_discount
        discount_amount, discounted_total = apply_discount(cart, request)

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'discount_amount': discount_amount,
        'discounted_total': discounted_total
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    
    if product.is_in_stock:
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            if cart_item.quantity < product.stock:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Added {product.name} to your cart.")
            else:
                messages.error(request, f"Sorry, only {product.stock} of {product.name} are in stock.")
        else:
            messages.success(request, f"Added {product.name} to your cart.")
    else:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
    
    return redirect('cart_detail')

def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0 and quantity <= cart_item.product.stock:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, f"Updated quantity of {cart_item.product.name}.")
            else:
                messages.error(request, f"Invalid quantity. Must be between 1 and {cart_item.product.stock}.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity. Please enter a valid number.")
    return redirect('cart_detail')

def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart_detail')

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
