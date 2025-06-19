from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from products.models import ProductView, Product

def get_personalized_recommendations(user, limit=5):
    """
    Generate personalized product recommendations for a given user based on their browsing history,
    purchase history, and cart interactions. The logic prioritizes products from categories the user
    has interacted with frequently, products co-viewed or co-purchased by similar users, and items
    related to their current interests.
    
    Args:
        user: The authenticated user for whom to generate recommendations.
        limit: Maximum number of recommended products to return (default: 5).
    
    Returns:
        A list of Product objects recommended for the user.
    """
    from orders.models import OrderItem
    from cart.models import CartItem
    
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

    # Step 1: Recommend products from the same categories, excluding already interacted products
    category_recommendations = Product.objects.filter(
        category_id__in=category_ids
    ).exclude(
        id__in=interacted_product_ids
    ).order_by('-created_at')[:limit]

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
