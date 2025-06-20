from django.db import models

class SalesAnalytics(models.Model):
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_orders = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_usage_count = models.PositiveIntegerField(default=0)
    discount_total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sales Analytics"

    def __str__(self):
        return f"Sales Analytics for {self.date.strftime('%Y-%m-%d')} - Revenue: {self.total_revenue}"


class CustomerAnalytics(models.Model):
    date = models.DateField(unique=True)
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    retention_rate = models.FloatField(default=0.0, help_text="Percentage of returning customers")
    average_customer_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Customer Analytics"

    def __str__(self):
        return f"Customer Analytics for {self.date.strftime('%Y-%m-%d')} - Total Customers: {self.total_customers}"


class ProductAnalytics(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    add_to_cart_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0, help_text="Percentage of views leading to purchase")
    abandonment_rate = models.FloatField(default=0.0, help_text="Percentage of add-to-cart not leading to purchase")
    stock_turnover_rate = models.FloatField(default=0.0, help_text="Rate at which stock is sold and replaced")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'date')
        verbose_name_plural = "Product Analytics"

    def __str__(self):
        return f"Product Analytics for {self.product.name} on {self.date.strftime('%Y-%m-%d')} - Views: {self.views}"


class MarketingAnalytics(models.Model):
    campaign = models.ForeignKey('promotions.Promotion', on_delete=models.CASCADE, related_name='analytics', null=True, blank=True)
    discount_code = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    impressions = models.PositiveIntegerField(default=0, help_text="Number of times campaign/discount was shown")
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0, help_text="Number of purchases attributed to campaign/discount")
    click_through_rate = models.FloatField(default=0.0, help_text="Percentage of impressions leading to clicks")
    conversion_rate = models.FloatField(default=0.0, help_text="Percentage of clicks leading to conversions")
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('campaign', 'discount_code', 'date')
        verbose_name_plural = "Marketing Analytics"
        constraints = [
            models.CheckConstraint(
                check=models.Q(campaign__isnull=False) | models.Q(discount_code__isnull=False),
                name='at_least_one_marketing_identifier'
            )
        ]

    def __str__(self):
        identifier = self.campaign.name if self.campaign else self.discount_code if self.discount_code else "General"
        return f"Marketing Analytics for {identifier} on {self.date.strftime('%Y-%m-%d')} - Conversions: {self.conversions}"


class WebsiteTraffic(models.Model):
    date = models.DateField(unique=True)
    total_visits = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0, help_text="Percentage of single-page visits")
    average_session_duration = models.FloatField(default=0.0, help_text="Average time spent per session in seconds")
    top_referral_source = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Website Traffic"

    def __str__(self):
        return f"Website Traffic for {self.date.strftime('%Y-%m-%d')} - Visits: {self.total_visits}"


class UserSegment(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='segment')
    segment_type = models.CharField(max_length=50, choices=[
        ('new', 'New User'),
        ('frequent_buyer', 'Frequent Buyer'),
        ('high_spender', 'High Spender'),
        ('budget_conscious', 'Budget Conscious'),
        ('inactive', 'Inactive')
    ], default='new')
    purchase_frequency = models.FloatField(default=0.0, help_text="Average purchases per month")
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_activity = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Segments"

    def __str__(self):
        return f"Segment for {self.user.username}: {self.get_segment_type_display()}"


class RecommendationInteraction(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='recommendation_interactions', null=True, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='recommendation_interactions')
    interaction_type = models.CharField(max_length=50, choices=[
        ('view', 'View'),
        ('click', 'Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase')
    ])
    recommendation_source = models.CharField(max_length=50, choices=[
        ('ml', 'Machine Learning'),
        ('session', 'Session-Based'),
        ('personalized', 'Personalized'),
        ('popular', 'Popular')
    ], default='personalized')
    interacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Recommendation Interactions"

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{self.get_interaction_type_display()} by {user_str} on {self.product.name} via {self.get_recommendation_source_display()}"
