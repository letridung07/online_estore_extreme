from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product
from products.recommendations import get_ml_recommendations
from django.core.cache import cache
import logging

class Command(BaseCommand):
    help = 'Pre-compute recommendations for frequent users to improve performance'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        self.stdout.write(self.style.SUCCESS('Starting pre-computation of recommendations...'))
        
        # Get active users (e.g., those with recent activity)
        active_users = User.objects.filter(is_active=True).order_by('-last_login')[:100]  # Limit to top 100 active users
        
        total_users = len(active_users)
        processed = 0
        
        for user in active_users:
            try:
                # Compute ML-based recommendations for the user
                recommendations = get_ml_recommendations(user, limit=10)
                if recommendations:
                    # Cache the recommendations with a 24-hour expiration
                    cache_key = f'recommendations:user:{user.id}'
                    cache.set(cache_key, [rec.id for rec in recommendations], timeout=60*60*24)
                    self.stdout.write(f'Pre-computed recommendations for user {user.username}')
                else:
                    self.stdout.write(f'No recommendations computed for user {user.username}')
            except Exception as e:
                logger.error(f'Error computing recommendations for user {user.username}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Error for user {user.username}: {str(e)}'))
            
            processed += 1
            if processed % 10 == 0:
                self.stdout.write(f'Processed {processed}/{total_users} users...')
        
        self.stdout.write(self.style.SUCCESS(f'Finished pre-computing recommendations for {total_users} users.'))
