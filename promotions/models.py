from django.db import models
from products.models import Product, Category

class Promotion(models.Model):
    PROMOTION_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        ('bogo', 'Buy One Get One'),
        ('free_shipping', 'Free Shipping'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Percentage or fixed amount depending on type")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum purchase amount for promotion to apply")
    products = models.ManyToManyField(Product, related_name='promotions', blank=True)
    categories = models.ManyToManyField(Category, related_name='promotions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_promotion_type_display()})"

    class Meta:
        verbose_name_plural = "Promotions"

class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=20, choices=(('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')))
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    usage_limit = models.PositiveIntegerField(default=1, help_text="Number of times this code can be used")
    times_used = models.PositiveIntegerField(default=0)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Discount Code: {self.code}"

    class Meta:
        verbose_name_plural = "Discount Codes"

class SaleEvent(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    products = models.ManyToManyField(Product, related_name='sale_events', blank=True)
    categories = models.ManyToManyField(Category, related_name='sale_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sale Event: {self.name} ({self.discount_percentage}% off)"

    class Meta:
        verbose_name_plural = "Sale Events"
