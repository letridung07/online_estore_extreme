from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from analytics.models import WebsiteTraffic

class Command(BaseCommand):
    help = 'Flushes cached website traffic data to the database'

    def handle(self, *args, **options):
        today = timezone.now().date()
        base_cache_key = f"website_traffic_{today}"
        
        # Get the current visit count and other metrics from cache
        visit_count = cache.get(base_cache_key, 0)
        unique_visitors = cache.get(f"{base_cache_key}_unique", 0)
        bounce_rate = cache.get(f"{base_cache_key}_bounce_rate", 0.0)
        session_duration = cache.get(f"{base_cache_key}_session_duration", 0.0)
        referral_source = cache.get(f"{base_cache_key}_referral_source", None)
        
        if visit_count > 0 or unique_visitors > 0:
            # Update or create the database record
            traffic, created = WebsiteTraffic.objects.get_or_create(date=today)
            # Update all available metrics
            traffic.total_visits += visit_count
            traffic.unique_visitors += unique_visitors
            if bounce_rate > 0.0:
                traffic.bounce_rate = bounce_rate
            if session_duration > 0.0:
                traffic.average_session_duration = session_duration
            if referral_source:
                traffic.top_referral_source = referral_source
            traffic.save()
            
            # Reset the cache counters for metrics that were flushed
            cache.set(base_cache_key, 0, timeout=None)
            if unique_visitors > 0:
                cache.set(f"{base_cache_key}_unique", 0, timeout=None)
            if bounce_rate > 0.0:
                cache.set(f"{base_cache_key}_bounce_rate", 0.0, timeout=None)
            if session_duration > 0.0:
                cache.set(f"{base_cache_key}_session_duration", 0.0, timeout=None)
            if referral_source:
                cache.set(f"{base_cache_key}_referral_source", None, timeout=None)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully flushed traffic data to database for {today}: {visit_count} visits, {unique_visitors} unique visitors"))
        else:
            self.stdout.write(self.style.WARNING(f"No traffic data to flush for {today}"))
