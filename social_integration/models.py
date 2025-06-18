from django.db import models
from products.models import Product

class SocialPlatform(models.Model):
    """
    Model to represent different social media platforms for integration.
    """
    name = models.CharField(max_length=50, unique=True)
    api_key = models.CharField(max_length=255, blank=True, help_text="API key for the platform")
    api_secret = models.CharField(max_length=255, blank=True, help_text="API secret for the platform")
    is_active = models.BooleanField(default=False, help_text="Is the integration active?")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Social Platform"
        verbose_name_plural = "Social Platforms"

class ProductSync(models.Model):
    """
    Model to track which products are synced to which social media platforms.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='social_syncs')
    platform = models.ForeignKey(SocialPlatform, on_delete=models.CASCADE, related_name='synced_products')
    synced_at = models.DateTimeField(auto_now=True)
    external_id = models.CharField(max_length=255, blank=True, help_text="External ID on the social platform")
    status = models.CharField(max_length=50, default='pending', choices=[
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ])

    def __str__(self):
        return f"{self.product.name} on {self.platform.name} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'platform'], name='unique_product_platform')
        ]
        verbose_name = "Product Sync"
        verbose_name_plural = "Product Syncs"
