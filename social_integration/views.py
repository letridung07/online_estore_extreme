from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SocialPlatform, ProductSync
from products.models import Product

# Social Platform Management Views
@login_required
def social_platform_list(request):
    """
    View to list all social media platforms and their integration status.
    """
    platforms = SocialPlatform.objects.all()
    return render(request, 'social_integration/social_platform_list.html', {'platforms': platforms})

@login_required
def social_platform_update(request, pk):
    """
    View to update social platform details such as API keys and activation status.
    """
    platform = get_object_or_404(SocialPlatform, pk=pk)
    if request.method == 'POST':
        platform.name = request.POST.get('name', platform.name)
        platform.api_key = request.POST.get('api_key', platform.api_key)
        platform.api_secret = request.POST.get('api_secret', platform.api_secret)
        platform.is_active = request.POST.get('is_active') == 'on'
        platform.save()
        messages.success(request, f"Updated {platform.name} integration settings.")
        return redirect('social_integration:social_platform_list')
    return render(request, 'social_integration/social_platform_update.html', {'platform': platform})

# Product Sync Management Views
@login_required
def product_sync_list(request):
    """
    View to list sync status of products across social platforms.
    """
    syncs = ProductSync.objects.all().select_related('product', 'platform')
    return render(request, 'social_integration/product_sync_list.html', {'syncs': syncs})

@login_required
def sync_product(request, product_id, platform_id):
    """
    View to initiate syncing a product to a specific social platform.
    """
    product = get_object_or_404(Product, pk=product_id)
    platform = get_object_or_404(SocialPlatform, pk=platform_id)
    
    if not platform.is_active:
        messages.error(request, f"Cannot sync to {platform.name}: Integration is not active.")
        return redirect('social_integration:product_sync_list')
    
    sync, created = ProductSync.objects.get_or_create(
        product=product,
        platform=platform,
        defaults={'status': 'pending'}
    )
    
    if not created and sync.status != 'failed':
        messages.info(request, f"{product.name} is already synced or pending sync to {platform.name}.")
        return redirect('social_integration:product_sync_list')
    
    # Placeholder for actual sync logic (e.g., API call to social platform)
    sync.status = 'pending'
    sync.save()
    messages.success(request, f"Initiated sync of {product.name} to {platform.name}.")
    return redirect('social_integration:product_sync_list')

@login_required
def retry_sync(request, sync_id):
    """
    View to retry a failed sync operation.
    """
    sync = get_object_or_404(ProductSync, pk=sync_id)
    if sync.status != 'failed':
        messages.info(request, f"Sync of {sync.product.name} to {sync.platform.name} is not in a failed state.")
        return redirect('social_integration:product_sync_list')
    
    # Placeholder for retry logic
    sync.status = 'pending'
    sync.save()
    messages.success(request, f"Retrying sync of {sync.product.name} to {sync.platform.name}.")
    return redirect('social_integration:product_sync_list')
