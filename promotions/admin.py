from django.contrib import admin
from .models import Promotion, DiscountCode, SaleEvent

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'promotion_type', 'value', 'start_date', 'end_date', 'is_active')
    list_filter = ('promotion_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active', 'times_used', 'usage_limit')
    list_filter = ('discount_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('code', 'description')
    date_hierarchy = 'start_date'

@admin.register(SaleEvent)
class SaleEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
