from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from .models import Product, Category, Review
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect

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
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort': sort,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    """
    View for displaying a single product's details with recommendations and reviews.
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Basic recommendation system: suggest products from the same category
    recommendations = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:3]
    
    if not recommendations:
        # Fallback to most popular products based on order frequency
        recommendations = Product.objects.annotate(order_count=Count('orderitem')).order_by('-order_count')[:3]
    
    # Fetch reviews for this product (limit to latest N for performance)
    reviews = product.reviews.order_by('-created_at')[:REVIEW_DISPLAY_LIMIT]
    average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
    
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
    }
    return render(request, 'products/product_detail.html', context)
