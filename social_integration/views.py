from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
import logging
from .models import SocialPlatform, ProductSync
from products.models import Product

# Set up logging for debugging and error tracking
logger = logging.getLogger(__name__)

# Social Platform Management Views
@login_required
@user_passes_test(lambda u: u.is_staff)
def social_platform_list(request):
    """
    View to list all social media platforms and their integration status.
    Restricted to staff users for security.
    """
    platforms = SocialPlatform.objects.all()
    return render(request, 'social_integration/social_platform_list.html', {'platforms': platforms})

@login_required
@user_passes_test(lambda u: u.is_staff)
def social_platform_update(request, pk):
    """
    View to update social platform details such as API keys and activation status.
    Restricted to staff users for security.
    """
    platform = get_object_or_404(SocialPlatform, pk=pk)
    if request.method == 'POST':
        try:
            platform.name = request.POST.get('name', platform.name)
            platform.api_key = request.POST.get('api_key', platform.api_key)
            platform.api_secret = request.POST.get('api_secret', platform.api_secret)
            platform.is_active = request.POST.get('is_active') == 'on'
            platform.full_clean()  # Validate model fields before saving
            platform.save()
            messages.success(request, f"Updated {platform.name} integration settings.")
            logger.info(f"Platform {platform.name} updated by user {request.user.username}")
            return redirect('social_integration:social_platform_list')
        except ValidationError as e:
            messages.error(request, f"Error updating {platform.name}: {str(e)}")
            logger.error(f"Validation error updating platform {platform.name}: {str(e)}")
    return render(request, 'social_integration/social_platform_update.html', {'platform': platform})

# Product Sync Management Views
@login_required
@user_passes_test(lambda u: u.is_staff)
def product_sync_list(request):
    """
    View to list sync status of products across social platforms.
    Restricted to staff users for security.
    """
    syncs = ProductSync.objects.all().select_related('product', 'platform')
    return render(request, 'social_integration/product_sync_list.html', {'syncs': syncs})

@login_required
@user_passes_test(lambda u: u.is_staff)
def sync_product(request, product_id, platform_id):
    """
    View to initiate syncing a product to a specific social platform.
    Restricted to staff users for security.
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
    
    try:
        # Generic framework for API interaction with social platform
        logger.info(f"Attempting to sync {product.name} to {platform.name}")
        if platform.api_key and platform.api_secret:
            # Simulate API authentication (replace with actual API call for specific platform)
            auth_success = True  # Placeholder for real authentication logic
            if auth_success:
                # Simulate sending product data (replace with actual data payload for specific platform)
                product_data = {
                    'name': product.name,
                    'description': getattr(product, 'description', ''),
                    # Add more fields like images if available in Product model
                }
                # Placeholder for API response (replace with actual API call result)
                api_response = {'success': True, 'external_id': f"ext_{product.id}_{platform.id}"}
                if api_response.get('success'):
                    sync.status = 'synced'
                    sync.external_id = api_response.get('external_id', '')
                    messages.success(request, f"Initiated sync of {product.name} to {platform.name}.")
                    logger.info(f"Sync successful for {product.name} to {platform.name} by {request.user.username}")
                else:
                    sync.status = 'failed'
                    messages.error(request, f"Failed to sync {product.name} to {platform.name}: API error")
                    logger.error(f"Sync failed for {product.name} to {platform.name}: API error")
            else:
                sync.status = 'failed'
                messages.error(request, f"Failed to authenticate with {platform.name} for syncing {product.name}.")
                logger.error(f"Authentication failed with {platform.name} for {product.name}")
        else:
            sync.status = 'failed'
            messages.error(request, f"Cannot sync to {platform.name}: API credentials missing.")
            logger.error(f"API credentials missing for {platform.name} when syncing {product.name}")
        sync.save()
    except Exception as e:
        sync.status = 'failed'
        sync.save()
        messages.error(request, f"Failed to initiate sync for {product.name} to {platform.name}: {str(e)}")
        logger.error(f"Sync failed for {product.name} to {platform.name}: {str(e)}")
    return redirect('social_integration:product_sync_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def retry_sync(request, sync_id):
    """
    View to retry a failed sync operation.
    Restricted to staff users for security.
    """
    sync = get_object_or_404(ProductSync, pk=sync_id)
    if sync.status != 'failed':
        messages.info(request, f"Sync of {sync.product.name} to {sync.platform.name} is not in a failed state.")
        return redirect('social_integration:product_sync_list')
    
    try:
        # Generic framework for retrying API interaction with social platform
        logger.info(f"Retrying sync for {sync.product.name} to {sync.platform.name}")
        if sync.platform.api_key and sync.platform.api_secret:
            # Simulate API re-authentication (replace with actual API call for specific platform)
            auth_success = True  # Placeholder for real authentication logic
            if auth_success:
                # Simulate resending product data or updating existing (replace with actual logic)
                product_data = {
                    'name': sync.product.name,
                    'description': getattr(sync.product, 'description', ''),
                    # Add more fields if available in Product model
                }
                # Placeholder for API response (replace with actual API call result)
                api_response = {'success': True, 'external_id': sync.external_id or f"ext_{sync.product.id}_{sync.platform.id}"}
                if api_response.get('success'):
                    sync.status = 'synced'
                    sync.external_id = api_response.get('external_id', '')
                    messages.success(request, f"Retrying sync of {sync.product.name} to {sync.platform.name} successful.")
                    logger.info(f"Retry sync successful for {sync.product.name} to {sync.platform.name} by {request.user.username}")
                else:
                    sync.status = 'failed'
                    messages.error(request, f"Failed to retry sync for {sync.product.name} to {sync.platform.name}: API error")
                    logger.error(f"Retry sync failed for {sync.product.name} to {sync.platform.name}: API error")
            else:
                sync.status = 'failed'
                messages.error(request, f"Failed to re-authenticate with {sync.platform.name} for retrying sync of {sync.product.name}.")
                logger.error(f"Re-authentication failed with {sync.platform.name} for {sync.product.name}")
        else:
            sync.status = 'failed'
            messages.error(request, f"Cannot retry sync to {sync.platform.name}: API credentials missing.")
            logger.error(f"API credentials missing for {sync.platform.name} when retrying sync of {sync.product.name}")
        sync.save()
    except Exception as e:
        sync.status = 'failed'
        sync.save()
        messages.error(request, f"Failed to retry sync for {sync.product.name} to {sync.platform.name}: {str(e)}")
        logger.error(f"Retry sync failed for {sync.product.name} to {sync.platform.name}: {str(e)}")
    return redirect('social_integration:product_sync_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def social_platform_create(request):
    """
    View to create a new social media platform integration.
    Restricted to staff users for security.
    """
    if request.method == 'POST':
        try:
            platform = SocialPlatform(
                name=request.POST.get('name'),
                api_key=request.POST.get('api_key', ''),
                api_secret=request.POST.get('api_secret', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            platform.full_clean()  # Validate model fields before saving
            platform.save()
            messages.success(request, f"Created new platform integration: {platform.name}.")
            logger.info(f"Platform {platform.name} created by user {request.user.username}")
            return redirect('social_integration:social_platform_list')
        except ValidationError as e:
            messages.error(request, f"Error creating platform: {str(e)}")
            logger.error(f"Validation error creating platform: {str(e)}")
    return render(request, 'social_integration/social_platform_create.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def sync_product_select(request):
    """
    View to select a product and platform for syncing.
    Restricted to staff users for security.
    """
    products = Product.objects.all()
    platforms = SocialPlatform.objects.filter(is_active=True)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        platform_id = request.POST.get('platform_id')
        if product_id and platform_id:
            return redirect('social_integration:sync_product', product_id=product_id, platform_id=platform_id)
        else:
            messages.error(request, "Please select both a product and a platform.")
    
    return render(request, 'social_integration/sync_product_select.html', {
        'products': products,
        'platforms': platforms
    })
