from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django_redis import get_redis_connection
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
        bounce_count = cache.get(bounces_key, 0)
        
        # Get unique visitors count directly from Redis
        redis_conn = get_redis_connection("default")
        unique_visitors_count = redis_conn.scard(unique_visitors_key)
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
            cache.set(bounces_key, 0, timeout=None)
            # Reset the Redis set for unique visitors
            redis_conn.delete(unique_visitors_key)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully flushed traffic data to database for {today}: {visit_count} visits, {unique_visitors_count} unique visitors, {bounce_rate:.2f}% bounce rate"))
        else:
            self.stdout.write(self.style.WARNING(f"No traffic data to flush for {today}"))
