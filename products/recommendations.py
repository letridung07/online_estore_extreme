from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from products.models import ProductView, Product

def get_personalized_recommendations(user, limit=5):
    """
    Generate personalized product recommendations for a given user based on their browsing history,
    purchase history, cart interactions, and user segment. The logic prioritizes products from categories
    the user has interacted with frequently, products co-viewed or co-purchased by similar users, and
    adjusts based on user segment for more tailored suggestions.
    
    Args:
        user: The authenticated user for whom to generate recommendations.
        limit: Maximum number of recommended products to return (default: 5).
    
    Returns:
        A list of Product objects recommended for the user.
    """
    from orders.models import OrderItem
    from cart.models import CartItem
    from analytics.models import UserSegment
    
    if not user.is_authenticated:
        return []

    # Initialize sets for product IDs from different interaction types
    viewed_product_ids = set()
    purchased_product_ids = set()
    cart_product_ids = set()

    # Get products the user has viewed, ordered by frequency and type of interaction
    user_views = ProductView.objects.filter(user=user).values('product_id', 'interaction_type').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:10]  # Limit to top 10 for performance
    
    for view in user_views:
        viewed_product_ids.add(view['product_id'])
    
    # Get products the user has purchased
    user_purchases = OrderItem.objects.filter(order__user=user).values('product_id').annotate(
        purchase_count=Count('id')
    ).order_by('-purchase_count')[:10]
    
    for purchase in user_purchases:
        purchased_product_ids.add(purchase['product_id'])
    
    # Get products in the user's cart
    user_cart_items = CartItem.objects.filter(cart__user=user).values('product_id')
    for item in user_cart_items:
        cart_product_ids.add(item['product_id'])
    
    # Combine all interacted product IDs for exclusion or weighting
    interacted_product_ids = viewed_product_ids.union(purchased_product_ids).union(cart_product_ids)
    
    if not interacted_product_ids:
        return []

    # Get categories of interacted products
    interacted_products = Product.objects.filter(id__in=interacted_product_ids)
    category_ids = interacted_products.values_list('category_id', flat=True).distinct()

    # Get user segment for tailored recommendations
    try:
        user_segment = UserSegment.objects.get(user=user)
        segment_type = user_segment.segment_type
        avg_order_value = user_segment.average_order_value
    except UserSegment.DoesNotExist:
        segment_type = 'new'
        avg_order_value = 0.00

    # Adjust recommendation logic based on user segment
    price_filter = {}
    if segment_type == 'high_spender':
        # High spenders might prefer premium products
        price_filter = {'price__gte': avg_order_value * 0.8} if avg_order_value > 0 else {}
    elif segment_type == 'budget_conscious':
        # Budget-conscious users might prefer lower-priced items
        price_filter = {'price__lte': avg_order_value * 1.2} if avg_order_value > 0 else {}

    # Step 1: Recommend products from the same categories, excluding already interacted products
    category_query = Product.objects.filter(
        category_id__in=category_ids,
        **price_filter
    ).exclude(
        id__in=interacted_product_ids
    )
    
    if segment_type == 'frequent_buyer':
        category_recommendations = category_query.order_by('-stock')[:limit]  # Prioritize in-stock for frequent buyers
    else:
        category_recommendations = category_query.order_by('-created_at')[:limit]

    if category_recommendations.count() >= limit:
        return list(category_recommendations)

    # Step 2: If not enough, find products co-viewed or co-purchased by other users
    co_interacted_product_ids = ProductView.objects.filter(
        product_id__in=interacted_product_ids
    ).exclude(
        user=user
    ).values('user_id').distinct().annotate(
        interaction_count=Count('product_id')
    ).order_by('-interaction_count')[:10]  # Limit to top co-interactors

    co_interacted_users = [ci['user_id'] for ci in co_interacted_product_ids]
    
    # Include co-purchased products by these users
    co_purchased = OrderItem.objects.filter(
        order__user__in=co_interacted_users
    ).exclude(
        product_id__in=interacted_product_ids
    ).values('product_id').annotate(
        purchase_count=Count('id')
    ).order_by('-purchase_count')[:limit - category_recommendations.count()]

    co_purchased_product_ids = [cp['product_id'] for cp in co_purchased]
    co_purchased_recommendations = Product.objects.filter(id__in=co_purchased_product_ids)

    # Include co-viewed products if still not enough
    remaining_limit = limit - category_recommendations.count() - co_purchased_recommendations.count()
    if remaining_limit > 0:
        co_viewed = ProductView.objects.filter(
            user_id__in=co_interacted_users
        ).exclude(
            product_id__in=interacted_product_ids
        ).values('product_id').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:remaining_limit]

        co_viewed_product_ids = [cv['product_id'] for cv in co_viewed]
        co_viewed_recommendations = Product.objects.filter(id__in=co_viewed_product_ids)
    else:
        co_viewed_recommendations = Product.objects.none()

    # Combine recommendations
    recommendations = list(category_recommendations) + list(co_purchased_recommendations) + list(co_viewed_recommendations)
    return recommendations[:limit]

def get_popular_products(limit=5, days=30):
    """
    Retrieve popular products based on view counts over a specified time period.
    This is useful for displaying trending or popular items to all users.
    
    Args:
        limit: Maximum number of popular products to return (default: 5).
        days: Number of past days to consider for view counts (default: 30).
    
    Returns:
        A list of Product objects that are the most viewed in the specified time frame.
    """
    time_threshold = timezone.now() - timedelta(days=days)
    popular_views = ProductView.objects.filter(
        viewed_at__gte=time_threshold
    ).values('product_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]

    popular_product_ids = [view['product_id'] for view in popular_views]
    return Product.objects.filter(id__in=popular_product_ids)

def get_ml_recommendations(user, limit=5):
    """
    Generate a hybrid product recommendation for a given user by combining personalized, popular, and session-based
    recommendations. This approach simulates a machine learning strategy by blending multiple existing methods
    to provide diverse and relevant suggestions without requiring external ML libraries.
    
    Args:
        user: The authenticated user for whom to generate recommendations.
        limit: Maximum number of recommended products to return (default: 5).
    
    Returns:
        A list of Product objects recommended for the user based on a hybrid approach.
    """
    from django.core.cache import cache
    
    if not user.is_authenticated:
        return get_personalized_recommendations(user, limit)
    
    # Check cache for pre-computed recommendations
    cache_key = f'recommendations:user:{user.id}'
    cached_recommendations = cache.get(cache_key)
    if cached_recommendations:
        return Product.objects.filter(id__in=cached_recommendations[:limit])
    
    # Since ML library installation is not feasible, use a hybrid approach
    # Combine results from personalized, popular, and session-based recommendations
    personalized_recs = get_personalized_recommendations(user, limit=limit * 2)
    popular_recs = get_popular_products(limit=limit * 2)
    
    # Blend recommendations by taking a mix from each source
    hybrid_recommendations = []
    used_product_ids = set()
    
    # Add from personalized recommendations first (prioritize user-specific)
    for rec in personalized_recs:
        if rec.id not in used_product_ids and len(hybrid_recommendations) < limit:
            hybrid_recommendations.append(rec)
            used_product_ids.add(rec.id)
    
    # Add from popular products if there's still room
    for rec in popular_recs:
        if rec.id not in used_product_ids and len(hybrid_recommendations) < limit:
            hybrid_recommendations.append(rec)
            used_product_ids.add(rec.id)
    
    # Cache the hybrid recommendations
    cache.set(cache_key, [rec.id for rec in hybrid_recommendations], timeout=60*60*24)
    
    return hybrid_recommendations[:limit]

def get_session_recommendations(request, limit=5):
    """
    Generate session-based product recommendations based on recent user actions within the current session.
    This function looks at products viewed or added to cart during the current session to suggest relevant items.
    
    Args:
        request: The HTTP request object containing session data.
        limit: Maximum number of recommended products to return (default: 5).
    
    Returns:
        A list of Product objects recommended based on session activity.
    """
    from django.contrib.sessions.models import Session
    from cart.models import CartItem
    
    session_key = request.session.session_key
    if not session_key:
        return []

    # Get recent product views from session (if tracked)
    viewed_product_ids = request.session.get('recently_viewed', [])
    if viewed_product_ids:
        viewed_product_ids = viewed_product_ids[-10:]  # Limit to last 10 viewed products
    
    # Get cart items for the current session
    cart_items = CartItem.objects.filter(cart__session_key=session_key)
    cart_product_ids = [item.product_id for item in cart_items]
    
    # Combine session-based interacted product IDs
    session_product_ids = set(viewed_product_ids + cart_product_ids)
    if not session_product_ids:
        return []
    
    # Get categories of session-interacted products
    session_products = Product.objects.filter(id__in=session_product_ids)
    category_ids = session_products.values_list('category_id', flat=True).distinct()
    
    # Recommend products from the same categories, excluding already interacted products
    recommendations = Product.objects.filter(
        category_id__in=category_ids
    ).exclude(
        id__in=session_product_ids
    ).order_by('-created_at')[:limit]
    
    return list(recommendations)
