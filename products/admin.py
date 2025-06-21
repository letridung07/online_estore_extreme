from django.contrib import admin
from .models import Category, Product, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'low_stock_status', 'category', 'auto_reorder_enabled', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'auto_reorder_enabled')
    search_fields = ('name', 'description')
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price', 'category', 'image')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold', 'supplier', 'reorder_quantity', 'auto_reorder_enabled')
        }),
    )
    
    def low_stock_status(self, obj):
        return obj.stock < obj.low_stock_threshold
    low_stock_status.boolean = True
    low_stock_status.short_description = 'Low Stock'

from .models import StockAlert

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'item_name', 'stock_level', 'status', 'created_at', 'updated_at')
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('product__name', 'variant__name')
    ordering = ('-created_at',)
    
    def item_name(self, obj):
        if obj.alert_type == 'product':
            return obj.product.name
        return f"{obj.variant.product.name} - {obj.variant.name}"
    item_name.short_description = 'Item'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_as_resolved.short_description = 'Mark selected alerts as resolved'
    actions = [mark_as_resolved]

from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('name', 'contact_email', 'phone_number')
    ordering = ('name',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('comment', 'product__name', 'user__username')
    ordering = ('-created_at',)

from .models import Variant

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price_adjustment', 'stock', 'low_stock_status', 'created_at', 'updated_at')
    list_filter = ('product', 'created_at')
    search_fields = ('name', 'product__name', 'sku')
    ordering = ('product', 'name')
    
    def low_stock_status(self, obj):
        return obj.stock < obj.low_stock_threshold
    low_stock_status.boolean = True
    low_stock_status.short_description = 'Low Stock'
