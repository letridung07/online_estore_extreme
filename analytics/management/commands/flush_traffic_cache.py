from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from analytics.models import WebsiteTraffic

class Command(BaseCommand):
    help = 'Flushes cached website traffic data to the database'

    def handle(self, *args, **options):
        today = timezone.now().date()
        total_visits_key = f"website_traffic_total_{today}"
        unique_visitors_key = f"website_traffic_unique_{today}"
        bounces_key = f"website_traffic_bounces_{today}"
        
        # Get the current visit count and other metrics from cache
        visit_count = cache.get(total_visits_key, 0)
        unique_visitors_set = cache.get(unique_visitors_key, set())
        bounce_count = cache.get(bounces_key, 0)
        
        unique_visitors_count = len(unique_visitors_set)
        bounce_rate = 0.0
        if visit_count > 0:
            bounce_rate = (bounce_count / visit_count) * 100 if bounce_count > 0 else 0.0
        
        if visit_count > 0 or unique_visitors_count > 0:
            # Update or create the database record
            traffic, created = WebsiteTraffic.objects.get_or_create(date=today)
            # Update all available metrics
            traffic.total_visits += visit_count
            traffic.unique_visitors += unique_visitors_count
            traffic.bounce_rate = bounce_rate
            traffic.save()
            
            # Reset the cache counters for metrics that were flushed
            cache.set(total_visits_key, 0, timeout=None)
            cache.set(unique_visitors_key, set(), timeout=None)
            cache.set(bounces_key, 0, timeout=None)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully flushed traffic data to database for {today}: {visit_count} visits, {unique_visitors_count} unique visitors, {bounce_rate:.2f}% bounce rate"))
        else:
            self.stdout.write(self.style.WARNING(f"No traffic data to flush for {today}"))
