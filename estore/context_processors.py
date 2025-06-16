from cart.models import Cart, CartItem

def cart_item_count(request):
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
    
    cart_item_count = 0
    if cart:
        cart_item_count = sum(item.quantity for item in cart.items.all())
    
    return {'cart_item_count': cart_item_count}
