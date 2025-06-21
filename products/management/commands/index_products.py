from django.core.management.base import BaseCommand
from products.models import Product
from products.search_indexes import index_product

class Command(BaseCommand):
    help = 'Indexes all products into Elasticsearch'

    def handle(self, *args, **options):
        self.stdout.write('Starting to index products...')
        products = Product.objects.all()
        total = products.count()
        indexed = 0

        for product in products:
            try:
                index_product(product)
                indexed += 1
                self.stdout.write(f'Indexed {indexed}/{total} products', ending='\r')
            except Exception as e:
                self.stderr.write(f'Error indexing product {product.id}: {str(e)}')

        self.stdout.write(self.style.SUCCESS(f'Successfully indexed {indexed} out of {total} products'))
