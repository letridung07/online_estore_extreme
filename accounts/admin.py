from django.contrib import admin
from .models import UserProfile, ShippingAddress

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('user__username', 'phone_number')

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line_1', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country')
    search_fields = ('address_line_1', 'city', 'user__username')
