from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from analytics.models import WebsiteTraffic

class Command(BaseCommand):
    help = 'Flushes cached website traffic data to the database'

    def handle(self, *args, **options):
        today = timezone.now().date()
        cache_key = f"website_traffic_{today}"
        
        # Get the current visit count from cache
        visit_count = cache.get(cache_key, 0)
        
        if visit_count > 0:
            # Update or create the database record
            traffic, created = WebsiteTraffic.objects.get_or_create(date=today)
            traffic.total_visits += visit_count
            traffic.save()
            
            # Reset the cache counter
            cache.set(cache_key, 0, timeout=None)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully flushed {visit_count} visits to database for {today}"))
        else:
            self.stdout.write(self.style.WARNING(f"No visits to flush for {today}"))
