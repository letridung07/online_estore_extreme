from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from products.models import ProductView, Product

def get_personalized_recommendations(user, limit=5):
    """
    Generate personalized product recommendations for a given user based on their browsing history.
    The logic prioritizes products from categories the user has viewed frequently and products
    co-viewed by other users who viewed the same products.
    
    Args:
        user: The authenticated user for whom to generate recommendations.
        limit: Maximum number of recommended products to return (default: 5).
    
    Returns:
        A list of Product objects recommended for the user.
    """
    if not user.is_authenticated:
        return []

    # Get products the user has viewed, ordered by frequency of views
    user_views = ProductView.objects.filter(user=user).values('product_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:10]  # Limit to top 10 viewed products for performance

    if not user_views:
        return []

    viewed_product_ids = [view['product_id'] for view in user_views]
    viewed_products = Product.objects.filter(id__in=viewed_product_ids)

    # Get categories of viewed products
    category_ids = viewed_products.values_list('category_id', flat=True).distinct()

    # Step 1: Recommend products from the same categories, excluding already viewed products
    category_recommendations = Product.objects.filter(
        category_id__in=category_ids
    ).exclude(
        id__in=viewed_product_ids
    ).order_by('-created_at')[:limit]

    if category_recommendations.count() >= limit:
        return list(category_recommendations)

    # Step 2: If not enough recommendations, find products co-viewed by other users
    co_viewed_product_ids = ProductView.objects.filter(
        product_id__in=viewed_product_ids
    ).exclude(
        user=user
    ).values('user_id').distinct().annotate(
        co_viewed_products=Count('product_id')
    ).order_by('-co_viewed_products')[:10]  # Limit to top co-viewers

    co_viewed_users = [cv['user_id'] for cv in co_viewed_product_ids]
    co_viewed_views = ProductView.objects.filter(
        user_id__in=co_viewed_users
    ).exclude(
        product_id__in=viewed_product_ids
    ).values('product_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit - category_recommendations.count()]

    co_viewed_product_ids = [cv['product_id'] for cv in co_viewed_views]
    co_viewed_recommendations = Product.objects.filter(id__in=co_viewed_product_ids)

    # Combine recommendations
    recommendations = list(category_recommendations) + list(co_viewed_recommendations)
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
