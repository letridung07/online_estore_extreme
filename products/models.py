from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock > 0


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"{self.rating} star review for {self.product.name} by {self.user.username}"


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="Variant name (e.g., 'Red', 'Large')")
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price difference from base product")
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True, blank=True, help_text="Stock Keeping Unit identifier")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Variants"
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def total_price(self):
        return self.product.price + self.price_adjustment

    @property
    def is_in_stock(self):
        return self.stock > 0


class ProductView(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('click', 'Click'),
        ('hover', 'Hover'),
        ('add_to_cart', 'Add to Cart'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='product_views', null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES, default='view')
    duration = models.PositiveIntegerField(default=0, help_text="Duration of interaction in seconds, if applicable")

    class Meta:
        verbose_name_plural = "Product Views"

    def __str__(self):
        return f"{self.interaction_type} of {self.product.name} by {self.user.username if self.user else 'Anonymous'} on {self.viewed_at.strftime('%Y-%m-%d')}"
