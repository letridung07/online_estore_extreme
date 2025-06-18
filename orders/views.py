from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from cart.views import get_cart
from .helpers import apply_discount
from promotions.models import DiscountCode

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty. Add items to your cart before checking out.")
        return redirect('cart_detail')
    
    discount_code = request.session.get('discount_code')
    discount_amount, discounted_total = apply_discount(cart, request)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        
        # Concatenate shipment information into a single string for shipping_address
        shipping_address = f"Full Name: {full_name}, Address: {address}, City: {city}, Postal Code: {postal_code}, Country: {country}"
        
        order = Order.objects.create(
            user=request.user,
            total_price=discounted_total,
            shipping_address=shipping_address,
            status='pending',
            discount_code=discount_code if discount_code else None
        )
        
        for item in cart.items.all():
            price = item.variant.total_price if item.variant else item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=price
            )
        
        # Initialize Stripe payment
        import stripe
        from django.conf import settings
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        from decimal import Decimal, ROUND_HALF_UP
        try:
            # Ensure discounted_total is a Decimal and quantize to 2 decimal places
            discounted_total_decimal = Decimal(str(discounted_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            amount_cents = int((discounted_total_decimal * 100).to_integral_value(rounding=ROUND_HALF_UP))
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,  # Amount in cents
                currency='usd',
                metadata={'order_id': str(order.id)},
                description=f"Order #{order.id} for {request.user.email}",
            )
            order.payment_intent_id = payment_intent.id
            order.save()
            
            # Cart clearing and discount code handling is now done in payments/views.py webhook after payment confirmation
                    
            # Handle saving card information if requested
            save_card = request.POST.get('save_card')
            if save_card and 'payment_method_id' in request.POST:
                from payments.models import SavedPaymentMethod
                payment_method_id = request.POST.get('payment_method_id')
                try:
                    payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
                    last_four_digits = payment_method.card.last4 if payment_method.type == 'card' else 'XXXX'
                    SavedPaymentMethod.objects.create(
                        user=request.user,
                        payment_method_type='credit_card',
                        last_four_digits=last_four_digits,
                        token=payment_method_id,
                        is_default=False
                    )
                    messages.success(request, "Your card has been saved for future purchases.")
                except stripe.error.StripeError:
                    messages.error(request, "Failed to save your card. Please try again.")
                    
            messages.success(request, f"Your order #{order.id} has been placed successfully! Payment processing initiated.")
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'discount_amount': discount_amount,
                'discounted_total': discounted_total,
                'client_secret': payment_intent.client_secret,
                'order_id': order.id,
                'payment_processing': True
            })
        except stripe.error.StripeError as e:
            order.status = 'failed'
            order.save()
            messages.error(request, f"Payment processing failed: {str(e)}. Please try again.")
            return redirect('cart_detail')
    
    # Check for saved payment methods
    saved_payment_methods = []
    if request.user.is_authenticated:
        from payments.models import SavedPaymentMethod
        saved_payment_methods = SavedPaymentMethod.objects.filter(user=request.user)
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'discount_amount': discount_amount,
        'discounted_total': discounted_total,
        'saved_payment_methods': saved_payment_methods,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})
