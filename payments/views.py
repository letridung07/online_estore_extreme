from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
import stripe
import json
from .models import SavedPaymentMethod
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def saved_payment_methods(request):
    payment_methods = SavedPaymentMethod.objects.filter(user=request.user)
    return render(request, 'payments/saved_payment_methods.html', {'payment_methods': payment_methods})

@login_required
def delete_payment_method(request, method_id):
    payment_method = get_object_or_404(SavedPaymentMethod, id=method_id, user=request.user)
    try:
        stripe.PaymentMethod.detach(payment_method.token)
        payment_method.delete()
        messages.success(request, "Payment method deleted successfully.")
    except stripe.error.StripeError as e:
        messages.error(request, f"Failed to delete payment method: {str(e)}")
    return redirect('saved_payment_methods')

def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'completed'
            order.save()
        except Order.DoesNotExist:
            pass
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'failed'
            order.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)
