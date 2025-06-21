from django.core.management.base import BaseCommand
from products.models import Product, Variant, StockAlert
from products.notifications import send_low_stock_notification
from products.signals import create_stock_alert_if_needed

class Command(BaseCommand):
    help = 'Check stock levels for all products and variants, creating alerts for low stock items.'

    def handle(self, *args, **options):
        self.stdout.write("Starting stock level check...")
        
        # Check Products
        products = Product.objects.all()
        product_alerts = 0
        for product in products:
            if product.stock < product.low_stock_threshold:
                alert = create_stock_alert_if_needed('product', product, product.stock)
                if alert:
                    product_alerts += 1
                    self.stdout.write(f"Created low stock alert for Product: {product.name} (Stock: {product.stock})")
        
        # Check Variants
        variants = Variant.objects.all()
        variant_alerts = 0
        for variant in variants:
            if variant.stock < variant.low_stock_threshold:
                alert = create_stock_alert_if_needed('variant', variant, variant.stock)
                if alert:
                    variant_alerts += 1
                    self.stdout.write(f"Created low stock alert for Variant: {variant} (Stock: {variant.stock})")
        
        self.stdout.write(self.style.SUCCESS(
            f"Stock level check completed. Created {product_alerts} product alerts and {variant_alerts} variant alerts."
        ))
