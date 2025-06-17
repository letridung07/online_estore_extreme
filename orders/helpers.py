from django.utils import timezone
from promotions.models import DiscountCode

def apply_discount(cart, request):
    """
    Apply a discount to the cart based on the discount code stored in the session.
    Returns a tuple of (discount_amount, discounted_total).
    """
    discount_code = request.session.get('discount_code')
    if not discount_code:
        return 0.0, cart.total_price
    
    try:
        discount = DiscountCode.objects.get(code=discount_code, is_active=True)
        now = timezone.now()
        if discount.start_date <= now <= discount.end_date:
            if discount.times_used < discount.usage_limit and cart.total_price >= discount.minimum_purchase:
                if discount.discount_type == 'percentage':
                    discount_amount = cart.total_price * (discount.discount_value / 100)
                else:  # fixed_amount
                    discount_amount = min(discount.discount_value, cart.total_price)
                discounted_total = cart.total_price - discount_amount
                return discount_amount, discounted_total
    except DiscountCode.DoesNotExist:
        pass
    
    return 0.0, cart.total_price
