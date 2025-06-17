from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Promotion, DiscountCode, SaleEvent
from cart.models import Cart

def apply_discount_code(request):
    if request.method == 'POST':
        code = request.POST.get('discount_code', '').strip()
        if not code:
            messages.error(request, "Please enter a discount code.")
            return redirect('cart_detail')
        
        try:
            discount = DiscountCode.objects.get(code=code, is_active=True)
            now = timezone.now()
            if discount.start_date <= now <= discount.end_date:
                if discount.times_used < discount.usage_limit:
                    cart = Cart.objects.get(user=request.user if request.user.is_authenticated else None, 
                                           session_key=request.session.session_key if not request.user.is_authenticated else None)
                    if cart.total_price >= discount.minimum_purchase:
                        request.session['discount_code'] = code
                        request.session.modified = True
                        messages.success(request, f"Discount code {code} applied successfully!")
                    else:
                        messages.error(request, f"Minimum purchase of {discount.minimum_purchase} required for this discount.")
                else:
                    messages.error(request, "This discount code has reached its usage limit.")
            else:
                messages.error(request, "This discount code is not currently valid.")
        except DiscountCode.DoesNotExist:
            messages.error(request, "Invalid discount code.")
        
        return redirect('cart_detail')
    return redirect('cart_detail')

def current_promotions(request):
    now = timezone.now()
    promotions = Promotion.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    sales = SaleEvent.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    
    context = {
        'promotions': promotions,
        'sales': sales,
    }
    return render(request, 'promotions/current_promotions.html', context)
