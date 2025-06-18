from django.contrib import admin
from .models import SocialPlatform, ProductSync

@admin.register(SocialPlatform)
class SocialPlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active',)
    list_filter = ('is_active',)
    search_fields = ('name',)
    fields = ('name', 'api_key', 'api_secret', 'is_active')
    ordering = ('name',)

@admin.register(ProductSync)
class ProductSyncAdmin(admin.ModelAdmin):
    list_display = ('product', 'platform', 'status', 'synced_at')
    list_filter = ('status', 'platform', 'synced_at')
    search_fields = ('product__name', 'platform__name', 'external_id')
    fields = ('product', 'platform', 'external_id', 'status')
    ordering = ('-synced_at',)
    readonly_fields = ('synced_at',)
