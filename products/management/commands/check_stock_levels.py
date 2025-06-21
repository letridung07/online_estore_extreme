from django.core.management.base import BaseCommand
from products.models import Product, Variant, StockAlert
from products.notifications import send_low_stock_notification

class Command(BaseCommand):
    help = 'Check stock levels for all products and variants, creating alerts for low stock items.'

    def handle(self, *args, **options):
        self.stdout.write("Starting stock level check...")
        
        # Check Products
        products = Product.objects.all()
        product_alerts = 0
        for product in products:
            if product.stock < product.low_stock_threshold:
                # Check if there's already a pending alert for this product
                recent_alert = StockAlert.objects.filter(
                    alert_type='product',
                    product=product,
                    status='pending'
                ).order_by('-created_at').first()
                
                if not recent_alert:
                    alert = StockAlert.objects.create(
                        alert_type='product',
                        product=product,
                        stock_level=product.stock,
                        status='pending'
                    )
                    send_low_stock_notification(alert)
                    product_alerts += 1
                    self.stdout.write(f"Created low stock alert for Product: {product.name} (Stock: {product.stock})")
        
        # Check Variants
        variants = Variant.objects.all()
        variant_alerts = 0
        for variant in variants:
            if variant.stock < variant.low_stock_threshold:
                # Check if there's already a pending alert for this variant
                recent_alert = StockAlert.objects.filter(
                    alert_type='variant',
                    variant=variant,
                    status='pending'
                ).order_by('-created_at').first()
                
                if not recent_alert:
                    alert = StockAlert.objects.create(
                        alert_type='variant',
                        variant=variant,
                        stock_level=variant.stock,
                        status='pending'
                    )
                    send_low_stock_notification(alert)
                    variant_alerts += 1
                    self.stdout.write(f"Created low stock alert for Variant: {variant} (Stock: {variant.stock})")
        
        self.stdout.write(self.style.SUCCESS(
            f"Stock level check completed. Created {product_alerts} product alerts and {variant_alerts} variant alerts."
        ))
