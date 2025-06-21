from elasticsearch_dsl import Document, Text, Integer, Float, Boolean, Keyword, Date, Nested, InnerDoc
from elasticsearch_dsl import connections
from django.conf import settings
from .models import Product, Category, Variant

# Define the Elasticsearch connection
connections.configure(**settings.ELASTICSEARCH_DSL)

class VariantDocument(InnerDoc):
    name = Text()
    price_adjustment = Float()
    stock = Integer()
    sku = Keyword()
    total_price = Float()
    is_in_stock = Boolean()

    class Meta:
        dynamic = 'strict'

class ProductDocument(Document):
    name = Text(analyzer='snowball', fields={'raw': Keyword()})
    description = Text(analyzer='snowball')
    price = Float()
    stock = Integer()
    category = Text(fields={'raw': Keyword()})
    category_id = Integer()
    image_url = Keyword()
    is_in_stock = Boolean()
    created_at = Date()
    updated_at = Date()
    variants = Nested(VariantDocument)

    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'snowball': {
                        'type': 'snowball',
                        'language': 'English'
                    }
                }
            }
        }

    class Meta:
        dynamic = 'strict'

    def save(self, **kwargs):
        return super().save(**kwargs)

    def prepare_category(self, instance):
        return instance.category.name if instance.category else ''

    def prepare_category_id(self, instance):
        return instance.category.id if instance.category else 0

    def prepare_image_url(self, instance):
        return instance.image.url if instance.image else ''

    def prepare_variants(self, instance):
        variants = []
        for variant in instance.variants.all():
            variants.append({
                'name': variant.name,
                'price_adjustment': float(variant.price_adjustment),
                'stock': variant.stock,
                'sku': variant.sku,
                'total_price': float(variant.total_price),
                'is_in_stock': variant.is_in_stock
            })
        return variants

def index_product(product):
    doc = ProductDocument(
        meta={'id': product.id},
        name=product.name,
        description=product.description,
        price=float(product.price),
        stock=product.stock,
        category=product.category.name if product.category else '',
        category_id=product.category.id if product.category else 0,
        image_url=product.image.url if product.image else '',
        is_in_stock=product.is_in_stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
        variants=[{
            'name': v.name,
            'price_adjustment': float(v.price_adjustment),
            'stock': v.stock,
            'sku': v.sku,
            'total_price': float(v.total_price),
            'is_in_stock': v.is_in_stock
        } for v in product.variants.all()]
    )
    doc.save()
    return doc
