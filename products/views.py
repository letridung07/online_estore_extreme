from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from .models import Product, Category

def product_list(request):
    """
    View for displaying a list of products with search and filtering capabilities.
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
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    """
    View for displaying a single product's details with recommendations.
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Basic recommendation system: suggest products from the same category
    recommendations = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:3]
    
    if not recommendations:
        # Fallback to most popular products based on order frequency
        recommendations = Product.objects.annotate(order_count=Count('orderitem')).order_by('-order_count')[:3]
    
    context = {
        'product': product,
        'recommendations': recommendations,
    }
    return render(request, 'products/product_detail.html', context)
