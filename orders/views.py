from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from cart.views import get_cart

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.all():
        messages.error(request, "Your cart is empty. Add items to your cart before checking out.")
        return redirect('cart_detail')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        
        shipping_address = f"{full_name}\n{address}\n{city}, {postal_code}\n{country}"
        
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price,
            shipping_address=shipping_address,
            status='pending'
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Clear the cart after successful order creation
        cart.items.all().delete()
        messages.success(request, f"Your order #{order.id} has been placed successfully!")
        return redirect('order_confirmation', order_id=order.id)
    
    return render(request, 'orders/checkout.html', {'cart': cart})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})
