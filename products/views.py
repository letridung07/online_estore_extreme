from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from .models import Product, Category, Review, ProductView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.http import JsonResponse
from products.recommendations import get_personalized_recommendations, get_popular_products # type: ignore

REVIEW_DISPLAY_LIMIT = 10  # Number of reviews to display per product

def product_list(request):
    """
    View for displaying a list of products with search, filtering, sorting, and pagination capabilities.
    """
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Handle category filter
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Handle price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Handle stock availability filter
    in_stock = request.GET.get('in_stock', '')
    if in_stock == 'true':
        products = products.filter(stock__gt=0)
    
    # Handle sorting
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'popular':
        products = products.annotate(order_count=Count('orderitem')).order_by('-order_count')
    else:
        # Default ordering: by name ascending (or adjust as needed)
        products = products.order_by('name')
    
    # Handle pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        products = paginator.page(paginator.num_pages)
    
    # Get popular products for display on the list page
    popular_products = get_popular_products(limit=5)
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort': sort,
        'popular_products': popular_products,
    }
    return render(request, 'products/product_list.html', context)

def record_product_view(product, user):
    """
    Helper function to record a product view.
    """
    if user.is_authenticated:
        ProductView.objects.create(product=product, user=user)
    else:
        ProductView.objects.create(product=product)

def product_detail(request, pk):
    """
    View for displaying a single product's details with recommendations and reviews.
    """
    from accounts.models import Wishlist, WishlistItem
    product = get_object_or_404(Product, pk=pk)

    # Record product view using helper
    record_product_view(product, request.user)

    # Get personalized recommendations for the user with A/B testing
    from products.recommendations import get_ml_recommendations, get_session_recommendations, get_personalized_recommendations
    from analytics.models import RecommendationInteraction
    import random

    # A/B Testing logic: Alternate between strategies for comparison
    test_group = random.choice(['ml', 'session', 'personalized'])
    request.session['recommendation_test_group'] = test_group
    request.session.modified = True

    if test_group == 'ml':
        recommendations = get_ml_recommendations(request.user, limit=5)
        source = 'ml'
    elif test_group == 'session':
        recommendations = get_session_recommendations(request, limit=5)
        source = 'session'
    else:
        recommendations = get_personalized_recommendations(request.user, limit=5)
        source = 'personalized'

    # Log the view interaction for analytics
    for rec in recommendations:
        RecommendationInteraction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            product=rec,
            interaction_type='view',
            recommendation_source=source
        )

    # Fetch reviews for this product (limit to latest N for performance)
    reviews = product.reviews.order_by('-created_at')[:REVIEW_DISPLAY_LIMIT]
    average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']

    # Check if product is in user's wishlist
    product_in_wishlist = False
    if request.user.is_authenticated:
        try:
            wishlist = request.user.wishlist.get()
            product_in_wishlist = WishlistItem.objects.filter(wishlist=wishlist, product=product).exists()
        except Wishlist.DoesNotExist:
            pass

    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            rating_int = None
        if rating_int and 1 <= rating_int <= 5:
            # Check if user has already reviewed this product
            if not Review.objects.filter(product=product, user=request.user).exists():
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=rating_int,
                    comment=comment
                )
                return redirect('product_detail', pk=product.pk)

    context = {
        'product': product,
        'recommendations': recommendations,
        'reviews': reviews,
        'average_rating': average_rating,
        'product_in_wishlist': product_in_wishlist,
    }
    return render(request, 'products/product_detail.html', context)


def add_to_comparison(request, product_id):
    """
    View to add a product to the comparison list stored in session data.
    Limits to 4 products for comparison.
    """
    product = get_object_or_404(Product, id=product_id)
    comparison_list = request.session.get('comparison_products', [])
    
    if product_id not in comparison_list:
        if len(comparison_list) < 4:
            comparison_list.append(product_id)
            request.session['comparison_products'] = comparison_list
            request.session.modified = True
            message = f"{product.name} has been added to comparison."
            status = "success"
        else:
            message = "You can compare up to 4 products only. Please remove one to add a new product."
            status = "error"
    else:
        message = f"{product.name} is already in your comparison list."
        status = "info"
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': status, 'message': message})
    else:
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))


def remove_from_comparison(request, product_id):
    """
    View to remove a product from the comparison list in session data.
    """
    comparison_list = request.session.get('comparison_products', [])
    product = get_object_or_404(Product, id=product_id)
    
    if product_id in comparison_list:
        comparison_list.remove(product_id)
        request.session['comparison_products'] = comparison_list
        request.session.modified = True
        message = f"{product.name} has been removed from comparison."
        status = "success"
    else:
        message = f"{product.name} was not in your comparison list."
        status = "info"
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': status, 'message': message})
    else:
        from django.urls import reverse
        return redirect(request.META.get('HTTP_REFERER', reverse('compare_products')))


def clear_comparison(request):
    """
    View to clear all products from the comparison list in session data.
    """
    request.session['comparison_products'] = []
    request.session.modified = True
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Comparison list cleared.'})
    else:
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))


def compare_products(request):
    """
    View to render the comparison page with selected products from session data.
    """
    comparison_list = request.session.get('comparison_products', [])
    products = Product.objects.filter(id__in=comparison_list) if comparison_list else []
    
    context = {
        'products': products,
    }
    return render(request, 'products/product_comparison.html', context)
